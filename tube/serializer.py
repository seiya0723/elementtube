from rest_framework import serializers
from .models import Video,VideoComment,VideoView,VideoMyList,VideoMyListFolder,VideoHistory,VideoGood,VideoBad,NotifyTarget,Activity

import datetime

class VideoSerializer(serializers.ModelSerializer):

    class Meta:
        model   = Video
        fields  = [ "category","title","description","content","user","thumbnail" ]


class VideoCommentSerializer(serializers.ModelSerializer):

    class Meta:
        model   = VideoComment
        fields  = [ "content","target","user"  ]

    def save(self, *args, **kwargs):
        if not self.instance:
            activity_calc(self.validated_data["user"].id, self.validated_data["target"].id, self.validated_data["target"].category.id, "comment",1)

        super().save(*args, **kwargs)


class ViewSerializer(serializers.ModelSerializer):

    class Meta:
        model   = VideoView
        fields  = [ "date","target","user","ip"  ]


    def save(self, *args, **kwargs):
        if not self.instance:
            #未ログインユーザーはIDがないためattribute Errorを引き起こす。その対策
            user_id     = None
            if self.validated_data["user"]:
                user_id = self.validated_data["user"].id 

            activity_calc(user_id, self.validated_data["target"].id, self.validated_data["target"].category.id, "play",1)

        super().save(*args, **kwargs)

class MyListFolderSerializer(serializers.ModelSerializer):

    class Meta:
        model   = VideoMyListFolder
        fields  = [ "title","description","user","public","search" ]

    #TODO:マイリストフォルダの作成上限

class MyListSerializer(serializers.ModelSerializer):

    class Meta:
        model   = VideoMyList
        fields  = [ "folder","target","user" ]

    def save(self, *args, **kwargs):
        if not self.instance:
            activity_calc(self.validated_data["user"].id, self.validated_data["target"].id, self.validated_data["target"].category.id, "mylist",1)

        super().save(*args, **kwargs)

    #TODO:マイリストの保存上限


class HistorySerializer(serializers.ModelSerializer):

    class Meta:
        model   = VideoHistory
        fields  = [ "target","user" ]


    #TODO:ここでセーブする時、青天井で履歴をセーブし続けるのは問題なので、一定数を超過すると、その数だけ削除する。
    #↑一人あたり50件とする。これはsettings.pyに書き込み、importして呼び出す。


#Goodに対しての変更か、Badに対しての変更化を判定する
class RateSerializer(serializers.Serializer):

    flag    = serializers.BooleanField()

class GoodSerializer(serializers.ModelSerializer):

    class Meta:
        model   = VideoGood
        fields  = [ "target","user"  ]

    def save(self, *args, **kwargs):
        if not self.instance:
            activity_calc(self.validated_data["user"].id, self.validated_data["target"].id, self.validated_data["target"].category.id, "good",1)

        super().save(*args, **kwargs)

class BadSerializer(serializers.ModelSerializer):

    class Meta:
        model   = VideoBad
        fields  = [ "target","user"  ]

    def save(self, *args, **kwargs):
        if not self.instance:
            activity_calc(self.validated_data["user"].id, self.validated_data["target"].id, self.validated_data["target"].category.id, "bad",1)

        super().save(*args, **kwargs)


#複数選択用
class UUIDListSerializer(serializers.Serializer):
    id_list = serializers.ListField( child=serializers.UUIDField() )


#together_uniqueを実装しているので、普通のモデルを継承したシリアライザでは既読処理は重複判定され、バリデーションNGになる。
#モデルとは紐付かないシリアライザを作る。
class NotifyTargetSerializer(serializers.Serializer):
    notify  = serializers.UUIDField()
    user    = serializers.UUIDField()


#モデルを継承しないフォームクラス
class YearMonthSerializer(serializers.Serializer):
    year    = serializers.IntegerField()
    month   = serializers.IntegerField()


class ActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model   = Activity
        fields  = [ "date","user","target","category","play","mylist","good","bad","comment" ]

def activity_calc(user,target,category,attr,add):

    date        = datetime.date.today()
    dic         = { "date":date, "user":user, "target":target, "category":category , "play":0, "mylist":0, "good":0, "bad":0, "comment":0 }
    instance    = Activity.objects.filter(user=user,target=target,category=category,date=date).first()

    if instance:
        print("追加加算処理")
        dic             = Activity.objects.filter(user=user,target=target,category=category,date=date).values().first()

        dic["user"]     = dic["user_id"]
        dic["target"]   = dic["target_id"]
        dic["category"] = dic["category_id"]
        dic[attr]       = dic[attr] + add

        serializer      = ActivitySerializer(instance,data=dic)

        if serializer.is_valid():
            print("OK")
            serializer.save()

    else:
        #無いのであれば必要なデータを加減算する処理
        print("新規作成後加算処理")

        dic[attr]   = dic[attr] + add
        serializer  = ActivitySerializer(data=dic)

        if serializer.is_valid():
            print("OK")
            serializer.save()

    print("完了")
