from rest_framework import status,views,response
from django.shortcuts import render,redirect

from django.conf import settings 
from django.db.models.functions import TruncMonth
from django.db.models import Q,Count,Sum
from django.http import HttpResponseNotAllowed
from django.http.response import JsonResponse
from django.template.loader import render_to_string

from django.contrib import messages
from django.core.paginator import Paginator
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone

from .models import ( Video,VideoCategory,VideoComment,VideoMyListFolder,VideoMyList,VideoHistory,VideoView,
        VideoGood,VideoBad,NotifyTarget,Notify,NewsCategory,News,Activity,Faq,Config )

from .serializer import ( VideoSerializer,VideoCommentSerializer,ViewSerializer,
        MyListSerializer,MyListFolderSerializer,HistorySerializer,YearMonthSerializer,
        RateSerializer,GoodSerializer,BadSerializer,UUIDListSerializer,NotifyTargetSerializer )

import magic,datetime

#トップページ関係
class IndexView(views.APIView):
    
    def distinct(self,obj,*args,**kwargs):
        id_list         = []
        new_objects     = []

        for o in obj:
            if o.id in id_list:
                continue
            new_objects.append(o)
            id_list.append(o.id)

        return new_objects
    
    def get(self,request,*args,**kwargs):

        context             = {}
        context["latests"]  = Video.objects.order_by("-dt")[:settings.DEFAULT_VIDEO_AMOUNT]

        if request.user.is_authenticated:
            context["histories"]    = VideoHistory.objects.filter(user=request.user.id).order_by("?")[:settings.DEFAULT_VIDEO_AMOUNT]
            context["goods"]        = self.distinct( Video.objects.filter(good=request.user.id).order_by("-dt")[:settings.DEFAULT_VIDEO_AMOUNT] )
            context["comments"]     = self.distinct( Video.objects.filter(comment=request.user.id).order_by("-dt")[:settings.DEFAULT_VIDEO_AMOUNT] ) 
            context["mylists"]      = self.distinct( Video.objects.filter(mylist=request.user.id).order_by("-dt")[:settings.DEFAULT_VIDEO_AMOUNT] ) 

        return render(request,"tube/index.html",context)

index   = IndexView.as_view()

#検索関係
class SearchView(views.APIView):

    def get(self,request,*args,**kwargs):

        context     = {}
        query       = Q()

        if "word" in request.GET:

            word    = request.GET["word"].replace("　"," ").split(" ")
            words   = [ w for w in word if w != "" ]

            for w in words:
                query &= Q( Q(title__icontains=w) | Q(description__icontains=w) )

        page        = 1
        if "page" in request.GET:
            page    = request.GET["page"]

        videos              = Video.objects.filter(query).order_by("-dt")
        context["amount"]   = len(videos)

        videos_paginator    = Paginator(videos,settings.SEARCH_AMOUNT_PAGE)
        context["videos"]   = videos_paginator.get_page(page)

        return render(request,"tube/search.html",context)

search  = SearchView.as_view()

#動画個別ページ
class SingleView(views.APIView):

    def get(self,request,video_pk,*args,**kwargs):

        context     = {}

        video       = Video.objects.filter(id=video_pk).first()
        if not video:
            return redirect("tube:index")
        context["video"]    = video
        
        #動画視聴回数加算と視聴履歴追加の処理
        self.add_view(request,video_pk)
        self.add_history(request,video_pk)

        comments_paginator          = Paginator( VideoComment.objects.filter(target=video_pk).order_by("-dt"), settings.COMMENTS_AMOUNT_PAGE )
        context["comments"]         = comments_paginator.get_page(1)

        context["already_good"]     = VideoGood.objects.filter(target=video_pk,user=request.user.id)
        context["already_bad"]      = VideoBad.objects.filter(target=video_pk,user=request.user.id)
        context["already_mylist"]   = VideoMyList.objects.filter(target=video_pk,user=request.user.id)

        context["relates"]          = Video.objects.filter(category=video.category).order_by("-dt")[:settings.DEFAULT_VIDEO_AMOUNT]

        context["categories"]       = VideoCategory.objects.all()

        return render(request,"tube/single.html",context)

    def add_view(self,request,video_pk,*args,**kwargs):
        dic             = {}

        if request.user.is_authenticated:
            dic["user"] = request.user.id
        else:
            dic["user"] = None

        #リクエストからIPアドレスを取得する方法
        #https://stackoverflow.com/questions/4581789/how-do-i-get-user-ip-address-in-django

        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')

        dic["ip"]       = ip
        dic["target"]   = video_pk
        dic["date"]     = datetime.date.today()

        serializer      = ViewSerializer(data=dic)
        if serializer.is_valid():
            serializer.save()

    def add_history(self,request,video_pk,*args,**kwargs):

        #TODO:非会員ユーザーはCookieに保存する仕組みでも良いのでは？←Cookieに動画IDを保存したとして、その他の情報はAjaxで実現するのか？かえって煩雑になるのでは？
        if request.user.is_authenticated:

            history = VideoHistory.objects.filter(user=request.user.id,target=video_pk).first()

            if history:
                #履歴の追加加算
                history.views   = history.views + 1
                history.dt      = timezone.now()
                history.save()
            else:
                #履歴の新規作成
                serializer      = HistorySerializer(data={"target":video_pk,"user":request.user.id})
                if serializer.is_valid():
                    serializer.save()

single  = SingleView.as_view()


#動画個別に対する、編集や投稿等の処理
class SingleModView(LoginRequiredMixin,views.APIView):

    #TODO:ここでコメントのページネーション？↑のクラス名変えるべきでは？
    def get(self,request,video_pk,*args,**kwargs):

        context     = {}
        json        = { "error":True }
        page        = 1
        if "page" in request.GET:
            page    = request.GET["page"]

        context["video"]    = Video.objects.filter(id=video_pk).first()
        comments            = VideoComment.objects.filter(target=video_pk).order_by("-dt")
        comments_paginator  = Paginator(comments,settings.COMMENTS_AMOUNT_PAGE)
        context["comments"] = comments_paginator.get_page(page)

        #コメントをrender_to_stringテンプレートを文字列化、JsonResponse
        json["content"] = render_to_string('tube/comments.html', context ,request)
        json["error"]   = False

        return JsonResponse(json)

    def post(self,request,video_pk,*args,**kwargs):

        copied              = request.POST.copy()
        copied["target"]    = video_pk
        copied["user"]      = request.user.id

        #instance    = VideoComment.objects.filter(id="").first()
        #serializer  = VideoCommentSerializer(instance,data=copied)

        serializer  = VideoCommentSerializer(data=copied)
        json        = {"json":True}

        if serializer.is_valid():
            serializer.save()
            context             = {}

            comments            = VideoComment.objects.filter(target=video_pk).order_by("-dt")
            comments_paginator  = Paginator(comments,settings.COMMENTS_AMOUNT_PAGE)
            context["comments"] = comments_paginator.get_page(1)
            context["video"]    = Video.objects.filter(id=video_pk).first()

            content             = render_to_string('tube/comments.html', context, request)

            json["error"]       = False
            json["message"]     = "投稿完了"
            json["content"]     = content
            
        else:
            print("バリデーションエラー")
            json["message"]     = "入力内容に誤りがあります。"
            json["content"]     = ""

        return JsonResponse(json)


    def patch(self,request,video_pk,*args,**kwargs):

        serializer  = RateSerializer(data=request.data)
        json        = {"error":True}

        if not serializer.is_valid():
            json["message"] = "入力内容に誤りがあります。"
            json["content"] = ""
            return JsonResponse(json)

        validated_data  = serializer.validated_data
        flag            = validated_data["flag"]

        #評価処理
        if flag:
            data    = VideoGood.objects.filter(user=request.user.id, target=video_pk).first()
        else:
            data    = VideoBad.objects.filter(user=request.user.id, target=video_pk).first()

        #評価の有無判定
        if data:
            data.delete()
            print("削除")
        else:
            #評価レコードが存在しない場合は新たに作る
            if flag:
                serializer  = GoodSerializer(data={ "user":request.user.id,"target":video_pk })
            else:
                serializer  = BadSerializer(data={ "user":request.user.id,"target":video_pk })

            if serializer.is_valid():
                print("保存")
                serializer.save()

        context                     = {}
        context["already_good"]     = VideoGood.objects.filter(target=video_pk,user=request.user.id)
        context["already_bad"]      = VideoBad.objects.filter(target=video_pk,user=request.user.id)
        context["already_mylist"]   = VideoMyList.objects.filter(target=video_pk,user=request.user.id)
        context["video"]            = Video.objects.filter(id=video_pk).first()

        json["content"] = render_to_string('tube/rate.html', context ,request)
        json["error"]   = False
        json["message"] = "投稿完了"

        return JsonResponse(json)

single_mod  = SingleModView.as_view()


#ランキング表示
class RankingView(views.APIView):

    #ランキング計算式
    def rank_calc(self,play,mylist,good,bad,comment):
        return play+mylist+good-bad+comment

    #モデルオブジェクトの状態をキープするため、重複をまとめてひとつのレコードに加算する
    def aggregate(self,obj,*args,**kwargs):

        #重複する動画IDがあれば、ひとつのアクティビティにまとめる(スコアを加算)。その時、ユーザー属性は削除
        id_list     = []
        new_objects = []

        initial     = Activity()

        for o in obj:
            if o.target.id in id_list:
                
                #一箇所にまとめる
                for n in new_objects:
                    if o.target.id == n.target.id:
                        #スコアを加算
                        n.score += o.score
                        break

                continue

            #この状態でアペンドすると、アクティビティに紐付いたユーザーの情報まで記録されるため、予め削除しておく。
            o.user  = initial.user
            new_objects.append(o)
            id_list.append(o.target.id)

        #ソーティング
        # https://stackoverflow.com/questions/2412770/good-ways-to-sort-a-queryset-django
        import operator

        return sorted(new_objects, key=operator.attrgetter('score'), reverse=True)


    def get(self,request,*args,**kwargs):

        context             = {}
        
        today               = datetime.date.today()
        yesterday           = today - datetime.timedelta(days=1)
        last_week           = today - datetime.timedelta(days=7)
        last_month          = today - datetime.timedelta(days=30)

        yesterday_query     = Q(date=yesterday)
        last_week_query     = Q(date__gte=last_week,date__lte=yesterday)
        last_month_query    = Q(date__gte=last_month,date__lte=yesterday)

        #同一動画の複数のレコードを1つに束ね、なおかつスコアが大きい順に並べる
        #ただし、valuesを使用しているため、辞書型になる。テンプレート側で動画タイトル、サムネイルの参照が通常のモデルオブジェクトとは違う。

        context["daily_all_ranks"]      = self.aggregate(Activity.objects.filter(yesterday_query).annotate( 
                                            score = self.rank_calc(play=Sum("play"),mylist=Sum("mylist"),good=Sum("good"),bad=Sum("bad"),comment=Sum("comment")) ).order_by()[:settings.LIMIT_RANK])
        context["weekly_all_ranks"]     = self.aggregate(Activity.objects.filter(last_week_query).annotate(
                                            score = self.rank_calc(play=Sum("play"),mylist=Sum("mylist"),good=Sum("good"),bad=Sum("bad"),comment=Sum("comment")) ).order_by()[:settings.LIMIT_RANK])
        context["monthly_all_ranks"]    = self.aggregate(Activity.objects.filter(last_month_query).annotate(
                                            score = self.rank_calc(play=Sum("play"),mylist=Sum("mylist"),good=Sum("good"),bad=Sum("bad"),comment=Sum("comment")) ).order_by()[:settings.LIMIT_RANK])

        context["daily_cate_ranks"]     = []
        context["weekly_cate_ranks"]    = []
        context["monthly_cate_ranks"]   = []

        categories                      = VideoCategory.objects.all()
        
        #カテゴリごとに検索してアペンド
        for category in categories:
            dic             = {}
            dic["category"] = category.name

            daily_dic       = dic.copy()
            weekly_dic      = dic.copy()
            monthly_dic     = dic.copy()

            cate_yesterday_query    = Q(category=category.id) & yesterday_query 
            cate_last_week_query    = Q(category=category.id) & last_week_query 
            cate_last_month_query   = Q(category=category.id) & last_month_query


            daily_dic["ranks"]      = self.aggregate(Activity.objects.filter(cate_yesterday_query).annotate(
                                        score = self.rank_calc(play=Sum("play"),mylist=Sum("mylist"),good=Sum("good"),bad=Sum("bad"),comment=Sum("comment")) ).order_by()[:settings.LIMIT_RANK])
            weekly_dic["ranks"]     = self.aggregate(Activity.objects.filter(cate_last_week_query).annotate(
                                        score = self.rank_calc(play=Sum("play"),mylist=Sum("mylist"),good=Sum("good"),bad=Sum("bad"),comment=Sum("comment")) ).order_by()[:settings.LIMIT_RANK])
            monthly_dic["ranks"]    = self.aggregate(Activity.objects.filter(cate_last_month_query).annotate(
                                        score = self.rank_calc(play=Sum("play"),mylist=Sum("mylist"),good=Sum("good"),bad=Sum("bad"),comment=Sum("comment")) ).order_by()[:settings.LIMIT_RANK])


            if daily_dic["ranks"]:
                context["daily_cate_ranks"].append(daily_dic)

            if weekly_dic["ranks"]:
                context["weekly_cate_ranks"].append(weekly_dic)

            if monthly_dic["ranks"]:
                context["monthly_cate_ranks"].append(monthly_dic)

        return render(request,"tube/rank/rank.html",context)

rank    = RankingView.as_view()

#マイページ表示
class MyPageView(LoginRequiredMixin,views.APIView):

    def distinct(self,obj,*args,**kwargs):
        id_list         = []
        new_objects     = []

        for o in obj:
            if o.id in id_list:
                continue
            new_objects.append(o)
            id_list.append(o.id)

        return new_objects

    def get(self,request,*args,**kwargs):

        #TODO:ここはページネーション仕様に別途ビューを作り、Ajaxで実現、ページ数だけでなく、各データごとに分岐させるためパラメータを余分にひとつ用意。
        context                     = {}
        context["videos"]           = Video.objects.filter(user=request.user.id).order_by("-dt")
        context["good_videos"]      = self.distinct( Video.objects.filter(good=request.user.id).order_by("-dt") )
        context["mylist_videos"]    = self.distinct( Video.objects.filter(mylist=request.user.id).order_by("-dt") )
        context["comment_videos"]   = self.distinct( Video.objects.filter(comment=request.user.id).order_by("-dt") )
        
        return render(request,"tube/mypage.html",context)

mypage  = MyPageView.as_view()


#TODO:投稿動画、良いねした動画等のページネーション
class MyPagePaginatorView(MyPageView):

    pass


class HistoryBaseView(LoginRequiredMixin,views.APIView):

    def distinct(self,obj,*args,**kwargs):

        id_list         = []
        new_objects     = []

        for o in obj:
            if o.target.id in id_list:
                continue
            new_objects.append(o)
            id_list.append(o.target.id)

        return new_objects

    #ここでcontextを返却、
    def select(self, request, *args,**kwargs):

        context                         = {}
        context["histories"]            = VideoHistory.objects.filter(user=request.user.id).order_by("-dt")
        context["good_histories"]       = self.distinct( VideoHistory.objects.filter(user=request.user.id,target__good=request.user.id).order_by("-dt") ) 
        context["mylist_histories"]     = self.distinct( VideoHistory.objects.filter(user=request.user.id,target__mylist=request.user.id).order_by("-dt") ) 
        context["comment_histories"]    = self.distinct( VideoHistory.objects.filter(user=request.user.id,target__comment=request.user.id).order_by("-dt") ) 

        return context

    #タブシステムとページネーションも考慮したrender_to_string
    #contextの値が不一致になってしまうので、render_to_stringはself.selectを発動すれば良いのでは？
    def render_to_string(self, request, page={}, *args, **kwargs):

        json    = {"error":True}

        context = self.select(request)
        target  = list(context.keys())

        for t in target:

            paginator       = Paginator(context[t],settings.SEARCH_AMOUNT_PAGE)
            if t in page:
                context[t]  = paginator.get_page(page[t])
            else:
                context[t]  = paginator.get_page(1)

            json[t]         = render_to_string('tube/partial/large_video_content_history.html', { "histories":context[t] }, request)

        return json

#閲覧履歴表示
class HistoryView(HistoryBaseView):

    def get(self,request,*args,**kwargs):

        #TODO:ここのページネーションの部分はマイリストに倣ってselectに含ませる
        context = self.select(request)
        target  = list(context.keys())

        #全て1ページ目を指定し、ページネーションに対応させる。
        for t in target:
            paginator   = Paginator(context[t],settings.SEARCH_AMOUNT_PAGE)
            context[t]  = paginator.get_page(1)




        return render(request,"tube/history.html",context)

    #ここは履歴の削除を(複数選択削除形式にする、リストのUUIDを判定するシリアライザ)
    def delete(self,request,*args,**kwargs):

        json        = {"error":True}
        serializer  = UUIDListSerializer(data=request.data)
    
        if not serializer.is_valid():
            print("ng")
            return JsonResponse(json)

        data        = serializer.validated_data
        histories   = VideoHistory.objects.filter(id__in=data["id_list"])
        histories.delete()

        #タブシステムとページネーション(削除後なので1ページ)を考慮したrender_to_string
        context         = self.select(request) 

        json            = self.render_to_string(request)
        json["error"]   = False

        return JsonResponse(json)

history = HistoryView.as_view()

#履歴のページ移動
class HistoryPaginatorView(HistoryBaseView):

    def get(self,request,*args,**kwargs):
        json    = {"error":True}
        context = self.select(request)

        #contextのキーを取り出し、そのページが含まれているかチェック。
        target  = list(context.keys())

        #TODO:ここで読み込むページの値をAjax側から受け取りする
        page    = {}
        for t in target:
            if t in request.GET:
                page[t] = request.GET[t]

        json            = self.render_to_string(request, page)
        json["error"]   = False

        return JsonResponse(json)

history_page    = HistoryPaginatorView.as_view()


#おすすめ動画表示
class RecommendView(LoginRequiredMixin,views.APIView):

    def get(self,request,*args,**kwargs):
        return render(request,"tube/recommend.html")

recommend   = RecommendView.as_view()

#通知表示
class NotifyView(LoginRequiredMixin,views.APIView):

    def get(self,request,*args,**kwargs):

        #アクセスしたユーザーの通知を
        notify_targets  = NotifyTarget.objects.filter(user=request.user.id).order_by("-dt")
        context         = { "notify_targets":notify_targets }

        return render(request,"tube/notify.html",context)


    def patch(self,request,*args,**kwargs):

        #既読処理
        json            = {"error":True}

        data            = request.data.copy()
        data["user"]    = request.user.id
        serializer      = NotifyTargetSerializer(data=data)

        if serializer.is_valid():
            validated   = serializer.validated_data
            
            #TIPS:notify_targetのidで指定すると、通知を受け取ったユーザー以外が既読にされてしまう可能性があるため、
            #unique_togetherを実装した場合、.first()でひとつだけでいい。
            notify_target   = NotifyTarget.objects.filter(notify=validated["notify"],user=validated["user"]).first()

            if notify_target:
                notify_target.read  = True
                notify_target.save()

                json["error"]       = False
                print("バリデーションOK")

        return JsonResponse(json)

    def delete(self,request,*args,**kwargs):
        json    = { "error":True }
        #TODO:ここに通知の削除機能を

        return JsonResponse(json)


notify  = NotifyView.as_view()

#マイリスト
class MyListView(LoginRequiredMixin,views.APIView):

    #マイリストのフォルダ一覧表示とページネーション
    def get(self,request,*args,**kwargs):

        context = {}
        context["contains"]     = VideoMyList.objects.filter(user=request.user.id,folder=None).count()
        context["typical"]      = VideoMyList.objects.filter(user=request.user.id,folder=None).order_by("-dt").first()

        #フォルダ毎にマイリスト数をカウントして追加。
        context["folders_full"] = VideoMyListFolder.objects.filter(user=request.user.id).annotate(contains=Count("videomylist")).order_by("-dt")
        paginator               = Paginator(context["folders_full"],settings.SEARCH_AMOUNT_PAGE)

        if "page" in request.GET:
            context["folders"]  = paginator.get_page(request.GET["page"])
        else:
            context["folders"]  = paginator.get_page(1)

        for f in context["folders"]:
            f.typical   = VideoMyList.objects.filter(user=request.user.id,folder=f.id).order_by("-dt").first()

        return render(request,"tube/mylist/mylist.html",context)

    def post(self,request,*args,**kwargs):

        context         = {}
        json            = {"error":True}
        copied          = request.POST.copy()
        copied["user"]  = request.user.id

        #TODO:登録数に上限を設定する。
        serializer  = MyListSerializer(data=copied)
        
        if serializer.is_valid():
            validated       = serializer.validated_data
            mylist          = VideoMyList.objects.filter(user=request.user.id,target=validated["target"],folder=None)

            #FIXME:ここで違うフォルダにマイリストする場合はOKとする。
            if not mylist:
                serializer.save()
            """
            else:
                mylist.delete()
            """

            #already_mylistによる装飾は廃止する
            context["already_good"]     = VideoGood.objects.filter(target=validated["target"].id,user=request.user.id)
            context["already_bad"]      = VideoBad.objects.filter(target=validated["target"].id,user=request.user.id)
            context["already_mylist"]   = VideoMyList.objects.filter(target=validated["target"].id,user=request.user.id)
            context["video"]            = Video.objects.filter(id=validated["target"].id).first()

            json["content"]             = render_to_string('tube/rate.html', context, request)
            json["error"]               = False


        return JsonResponse(json)

    #マイリストの複数選択削除
    def delete(self,request,*args,**kwargs):
        json        = { "error":True }

        serializer  = UUIDListSerializer(data=request.data)
        if not serializer.is_valid():
            print("ng")
            return JsonResponse(json)

        data        = serializer.validated_data
        mylists     = VideoMyList.objects.filter(id__in=data["id_list"])
        mylists.delete()

        json["error"]   = False

        return JsonResponse(json)

mylist  = MyListView.as_view()

#フォルダ内のマイリストの表示
class MyListFolderView(LoginRequiredMixin,views.APIView):

    def get(self, request, *args, **kwargs):

        context                 = {}
        context["folders"]      = VideoMyListFolder.objects.filter(user=request.user.id).order_by("-dt")

        if "folder_pk" not in kwargs:
            context["folder"]   = VideoMyListFolder()
            context["mylists"]  = VideoMyList.objects.filter(user=request.user.id, folder=None).order_by("-dt")
        else:
            context["folder"]   = VideoMyListFolder.objects.filter(id=kwargs["folder_pk"],user=request.user.id).first()
            context["mylists"]  = VideoMyList.objects.filter(user=request.user.id, folder=kwargs["folder_pk"]).order_by("-dt")

        paginator               = Paginator(context["mylists"],settings.SEARCH_AMOUNT_PAGE)

        #ここでページネーション
        if "page" in request.GET:
            context["mylists"]  = paginator.get_page(request.GET["page"])
        else:
            context["mylists"]  = paginator.get_page(1)

        return render(request,"tube/mylist/mylist_folder.html",context)


    #マイリストフォルダの新規作成
    def post(self, request, *args, **kwargs):

        copied          = request.POST.copy()
        copied["user"]  = request.user.id 

        serializer      = MyListFolderSerializer(data=copied)

        if serializer.is_valid():
            serializer.save()

        return redirect("tube:mylist")


    #マイリストフォルダの削除。CASCADEになっているので、クライアントにはフォルダを削除すると中に登録されているマイリストも削除される旨を言う。
    def delete(self, request, *args, **kwargs):

        json    = {"error":True}

        if "folder_pk" not in kwargs:
            return JsonResponse(json)

        folder = VideoMyListFolder.objects.filter(id=kwargs["folder_pk"]).first()
        print("フォルダを削除する。")
        #folder.delete()

        json["error"]   = False

        return JsonResponse(json)

    #マイリストフォルダの編集(タイトル、説明文など)
    def put(self, request, *args, **kwargs):
        json    = {"error":True}
        
        if "folder_pk" not in kwargs:
            return JsonResponse(json)
        
        instance    = VideoMyListFolder.objects.filter(id=kwargs["folder_pk"]).first()

        if not instance:
            return JsonResponse(json)

        print(request.data)

        serializer  = MyListFolderSerializer(instance,data=request.data)

        if serializer.is_valid():
            serializer.save()

        json["error"]   = False

        return JsonResponse(json)

    #マイリストを別のマイリストフォルダへ移動する
    def patch(self, request, *args, **kwargs):

        json    = { "error":True }

        #マイリスト動画のUUIDのリストと、移動先のフォルダのUUIDの2つをバリデーション
        if "folder_pk" not in kwargs:
            return JsonResponse(json)

        #指定したフォルダが存在しなければエラー
        folder  = VideoMyListFolder.objects.filter(id=kwargs["folder_pk"]).first()
        if not folder:
            return JsonResponse(json)

        #選択されたUUIDのリストをバリデーション
        serializer  = UUIDListSerializer(data=request.data)
        if not serializer.is_valid():
            print("ng")
            return JsonResponse(json)

        #移動後のフォルダUUIDを格納
        folder_ids  = []
        folder_ids.append( folder.id )

        data        = serializer.validated_data
        mylists     = VideoMyList.objects.filter(id__in=data["id_list"]).values()

        #HACK:ここもう少し簡略化できないだろうか？
        for m in mylists:
            dic             = {}
            dic["folder"]   = folder.id
            dic["target"]   = m["target_id"]
            dic["user"]     = m["user_id"]

            #編集対象のマイリストを特定
            instance    = VideoMyList.objects.filter(id=m["id"]).first()

            #マイリストフォルダを編集
            serializer  = MyListSerializer(instance,data=dic)

            if serializer.is_valid():
                print("OK")
                serializer.save()
        
                #移動前のフォルダUUIDを格納(重複は許さない)
                if m["folder_id"] not in folder_ids:
                    folder_ids.append(m["folder_id"])

        print(folder_ids)

        json["error"]   = False

        return JsonResponse(json)

mylist_folder   = MyListFolderView.as_view()


#アップロード
class UploadView(LoginRequiredMixin,views.APIView):

    def get(self,request,*args,**kwargs):
        
        context     = {}

        context["categories"]   = VideoCategory.objects.all()
        context["limit_size"]   = settings.LIMIT_SIZE_MB
        context["allowed_mime"] = settings.ALLOWED_MIME_STR

        return render(request,"tube/upload.html",context)

    def post(self,request,*args,**kwargs):

        json    = {"error":True}
    
        """
        print(request.data)
        """
        request.data["user"]    = request.user.id
        serializer              = VideoSerializer(data=request.data)

        if not serializer.is_valid():
            json["message"]     = "入力内容に誤りがあります。"
            return JsonResponse(json)

        validated   = serializer.validated_data

        #TODO:ここのcontentキー参照。バリデーション結果から参照するべきでは？
        mime_type               = magic.from_buffer(validated["content"].read(1024) , mime=True)
        print(mime_type)

        """
        print(validated["content"].size)
        print(type(validated["content"].size))
        """

        if validated["content"].size >= settings.LIMIT_SIZE:
            json["message"] = "ファイルの上限容量は" + settings.LIMIT_SIZE_MB + "MBです。"
            return JsonResponse(json)
        
        #一時的に全てのMIMEを受け入れる
        """
        if mime_type not in settings.ALLOWED_MIME:
            json["message"] = "投稿できるファイルは" + settings.ALLOWED_MIME_STR + "です。"
            return JsonResponse(json)
        """

        json["message"]     = "アップロードは完了しました。"
        json["error"]       = False

        return JsonResponse(json)

    def put(self,request,*args,**kwargs):

        #TODO:投稿動画の編集機能を実装する

        return JsonResponse(json)

upload  = UploadView.as_view()

#設定
class ConfigView(LoginRequiredMixin,views.APIView):

    def get(self,request,*args,**kwargs):

        context = {}
        context["config"]   = Config.objects.filter(user=request.user.id).first()
        
        return render(request,"tube/config.html",context)

    def post(self,request,*args,**kwargs):

        config  = Config.objects.filter(user=request.user.id).first()

        #あれば編集、なければ新規作成
        if config:
            form    = ConfigForm(request.POST,instance=config)
        else:
            form    = ConfigForm(request.POST)

        if form.is_valid():
            messages.info(request, "設定を変更しました")
            form.save()
        else:
            messages.info(request, "設定変更に失敗しました")

        return redirect("tube:config")


config  = ConfigView.as_view()


#ヘルプ
class HelpView(views.APIView):

    def get(self,request,*args,**kwargs):

        context         = {}
        context["faqs"] = Faq.objects.all()
        
        return render(request,"tube/help.html",context)

    def post(self,request,*args,**kwargs):

        #お問い合わせの受付
        form    = ContactForm(request.POST)

        if form.is_valid():
            messages.info(request, "お問い合わせを送信しました")
            form.save()
        else:
            messages.info(request, "お問い合わせの送信に失敗しました")
        
        return render(request,"tube/help.html")

help    = HelpView.as_view()


class NewsView(views.APIView):

    def get(self,request,*args,**kwargs):

        context                 = {}
        context["monthly"]      = News.objects.annotate(monthly_dt=TruncMonth('dt')).values('monthly_dt').annotate(num=Count('id')).values('monthly_dt', 'num').order_by("-monthly_dt")
        context["categories"]   = NewsCategory.objects.annotate(num=Count("news"))
        context["latests"]      = News.objects.all().order_by("-dt")[:10]

        if "news_pk" in kwargs:
            article = News.objects.filter(id=kwargs["news_pk"]).first()

            if not article:
                return redirect("tube:news")
                
            context["article"]  = article
            return render(request, "tube/news.html", context)

        
        #検索処理
        if "search" in request.GET:
            search      = request.GET["search"]

            if search == "" or search.isspace():
                return redirect("tube:news")

            search      = search.replace("　"," ").split(" ")
            searches    = [ w for w in search if w != "" ]

            query       = Q() 
            for w in searches:
                query &= Q( Q(title__contains=w) | Q(content__contains=w) ) 

            articles    = News.objects.filter(query).order_by("-dt")
        
        #月別アーカイブ
        elif "month" in request.GET and "year" in request.GET:
            serializer  = YearMonthSerializer(data=request.GET)

            if not serializer.is_valid():
                return redirect("tube:news")

            validated   = serializer.validated_data
            articles    = News.objects.filter(dt__year=validated["year"],dt__month=validated["month"]).order_by("-dt")

        #カテゴリ検索
        elif "category" in request.GET:
            category    = request.GET["category"]
            articles    = News.objects.filter(category__name=category).order_by("-dt")
            
        #未指定
        else:
            articles    = News.objects.all().order_by("-dt")

        #ページネーション
        paginator       = Paginator(articles,4)
        page            = 1
        if "page" in request.GET:
            page        = request.GET["page"]

        context["articles"]     = paginator.get_page(page)
        
        return render(request, "tube/news.html", context)

news    = NewsView.as_view()


class RuleView(views.APIView):

    def get(self,request,*args,**kwargs):
        #TODO:ここで管理サイトで入力したサイト名を表示させる

        return render(request, "tube/rule.html")

rule    = RuleView.as_view()






