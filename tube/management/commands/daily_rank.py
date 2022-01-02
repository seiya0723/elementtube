from django.core.management.base import BaseCommand


from ...models import Activity,DailyRank,WeeklyRank,MonthlyRank
from ...serializer import DailyRankSerializer

import datetime

class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        print("これでコマンドが実行できる。")
        today       = datetime.date.today()
        yesterday   = today - datetime.timedelta(days=1)

        dailies     = []
        #activities  = Activity.objects.filter(date=yesterday)
        activities  = Activity.objects.filter(date=today)


        raw_dic     = { "target":"","category":"","date":"","score":0,"rank":0 }

        #昨日のアクティビティから今日の集計処理を実行
        for activity in activities:
            dic     = raw_dic.copy()
            exist   = False
            
            #ここで1レコードのスコアを計算する。(TODO:後に視聴履歴、マイリスト等の重みも考慮して)
            score   = activity.play + activity.mylist + activity.good - activity.bad + activity.comment
            #score   = activity.play + activity.mylist + activity.good + activity.comment



            #既にdailiesに追加されている場合、そのまま追加加算
            for daily in dailies:
                if activity.target.id == daily["target"]:

                    #スコアの追加加算処理をして、ループを抜ける
                    daily["score"]  = daily["score"] + score
                    exist           = True
                    break
           
            #新規作成
            if not exist:
                dic["target"]       = activity.target.id
                dic["category"]     = activity.target.category.id
                dic["date"]         = today
                dic["score"]        = score

                dailies.append(dic)

        print(raw_dic)                
        print(dic)                


        #=======カテゴリごとのランク付け=========
        """
        #1. まずカテゴリごとに辞書型のリスト型の辞書型に仕分け
        #2. それぞれソーティングする。
        #3. カテゴリでループした後、カテゴリごとでランク付け、
        """

        #category_rank  = { category_uuid : [ {},{},{}, ] }
        #category_rank   = sorted(dailies, key=lambda x:x["score"], reverse=True)


        #TODO:カテゴリごとにするには？
        """
        辞書型のリスト型の辞書型にすれば良い。
        { category_uuid : [ {},{},{}, ] }
        """
       

        
        """
        #辞書型はイミュータブルなデータであるため、代入を行う時はcopy()メソッドで
        category_data   = []
        for daily in dailies:
            dic = daily.copy()
            category_data.append(dic)

    
        category_rank   = {}
        for daily in category_data:

            print(str(daily["category"]))
            print(daily["category"])
            print(daily)


            if daily["category"] in category_rank:
                category_rank[str(daily["category"])].append(daily)
            else:
                category_rank[str(daily["category"])]    = [ daily ]
        """

        #カテゴリランキングは同率はもう無視で良いのでは？order_byでやったほうが早いのでは？





        #=========総合ランキングのランク付け========



        #辞書型はイミュータブルなデータであるため、代入を行う時はcopy()メソッドで
        overall_data   = []
        for daily in dailies:
            dic = daily.copy()
            overall_data.append(dic)


        #全てのデイリーデータを集計し終わったら、ランクを指定する
        #参照元: https://qiita.com/yousuke_yamaguchi/items/23014a3c8d8beb8ba073
        overall_rank    = sorted(overall_data, key=lambda x:x["score"], reverse=True)
    
        #全てのデータを手に入れたらDailyRankに1つずつ挿入する。(スコアが同率であれば順位同じ、タイの数だけ1つ下の順位に加算する)

        length          = len(overall_rank)
        before_score    = 0
        current_rank    = 0
        tie             = 0

        for i in range(length):
            #overall_rank[i]["category"] = ""

            if before_score == overall_rank[i]["score"]:
                overall_rank[i]["rank"] = current_rank
                tie                     = tie + 1

            else:
                current_rank            = current_rank + tie + 1
                tie                     = 0
                overall_rank[i]["rank"] = current_rank
                before_score            = overall_rank[i]["score"]  



        print(overall_rank)

        #TODO:ここでDailyRankFormを使ってバリデーションをして挿入する。

        for rank in overall_rank:
            serializer  = DailyRankSerializer(data=rank)

            if serializer.is_valid():
                print("バリデーションOK")
            else:
                print("NG")
        



        
