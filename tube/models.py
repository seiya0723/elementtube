from django.db import models
from django.utils import timezone
from django.conf import settings
from django.core.validators import MinValueValidator,MaxValueValidator

import uuid, datetime

#TODO:カテゴリの初期データのjsonを用意しておく。loaddataで即運用できるようにする。
class VideoCategory(models.Model):

    class Meta:
        db_table    = "video_category"

    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name        = models.CharField(verbose_name="動画カテゴリ名",max_length=10)

    def __str__(self):
        return self.name

class Video(models.Model):

    class Meta:
        db_table    = "video"

    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    category    = models.ForeignKey(VideoCategory,verbose_name="動画カテゴリ",on_delete=models.PROTECT)
    dt          = models.DateTimeField(verbose_name="投稿日",default=timezone.now)
    title       = models.CharField(verbose_name="動画タイトル",max_length=50)
    description = models.CharField(verbose_name="動画説明文",max_length=300)
    content     = models.FileField(verbose_name="動画",upload_to="tube/video/")
    thumbnail   = models.ImageField(verbose_name="サムネイル",upload_to="tube/thumbnail/",blank=True)
    
    user        = models.ForeignKey(settings.AUTH_USER_MODEL,verbose_name="投稿者",on_delete=models.CASCADE,related_name="video_user")

    #TODO:課金して、どんな人がマイリスト、視聴したのかを確認できるようにするのは？これでグーグルAnalyticsの動画版を実現できる
    good        = models.ManyToManyField(settings.AUTH_USER_MODEL,verbose_name="良いね",through="VideoGood",related_name="video_good")
    bad         = models.ManyToManyField(settings.AUTH_USER_MODEL,verbose_name="悪いね",through="VideoBad",related_name="video_bad")
    comment     = models.ManyToManyField(settings.AUTH_USER_MODEL,verbose_name="コメント",through="VideoComment",related_name="video_comment")
    mylist      = models.ManyToManyField(settings.AUTH_USER_MODEL,verbose_name="マイリスト",through="VideoMylist",related_name="video_mylist")
    history     = models.ManyToManyField(settings.AUTH_USER_MODEL,verbose_name="視聴履歴",through="VideoHistory",related_name="video_history")

    #視聴履歴と再生回数は一緒くたにできない(同じ人が何度も再生して再生回数を水増しできないようにするため。
    #CAUTION:このviewはユーザーモデルに紐付いているので、video.view.allを実行してもユーザーIDがNullの非会員の再生を取りこぼす。あくまでも解析用
    view        = models.ManyToManyField(settings.AUTH_USER_MODEL,verbose_name="再生",through="VideoView",related_name="video_view")

    #再生回数の計測をする。(これは非会員ユーザーもカウントした値になる。)
    def view_true(self):
        return VideoView.objects.filter(target=self.id)


    def __str__(self):
        return self.title

#動画の再生を記録するモデル
class VideoView(models.Model):

    class Meta:
        db_table        = "video_view"
        unique_together = (("target","date","user"),("target","date","ip"))

    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    #↓バリデーション時ユニーク判定に失敗するので、再生日はビューが代入すること。
    date        = models.DateField(verbose_name="再生日")
    target      = models.ForeignKey(Video,verbose_name="再生する動画",on_delete=models.CASCADE)
    user        = models.ForeignKey(settings.AUTH_USER_MODEL,verbose_name="再生した人",on_delete=models.CASCADE,null=True,blank=True)
    ip          = models.GenericIPAddressField(verbose_name="再生した人のIPアドレス")


class VideoComment(models.Model):

    class Meta:
        db_table    = "video_comment"

    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    dt          = models.DateTimeField(verbose_name="投稿日時",default=timezone.now)
    content     = models.CharField(verbose_name="コメント",max_length=200)
    target      = models.ForeignKey(Video,verbose_name="コメント先の動画",on_delete=models.CASCADE)
    user        = models.ForeignKey(settings.AUTH_USER_MODEL,verbose_name="投稿者",on_delete=models.CASCADE)

    def __str__(self):
        return self.content

class VideoHistory(models.Model):

    class Meta:
        db_table    = "video_history"

    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    dt          = models.DateTimeField(verbose_name="視聴日時",default=timezone.now)
    target      = models.ForeignKey(Video,verbose_name="視聴した動画",on_delete=models.CASCADE)
    user        = models.ForeignKey(settings.AUTH_USER_MODEL,verbose_name="視聴したユーザー",on_delete=models.CASCADE)
    views       = models.IntegerField(verbose_name="視聴回数",default=1,validators=[MinValueValidator(1)])

    def __str__(self):
        return self.target.title

class VideoMyListFolder(models.Model):
    class Meta:
        db_table    = "video_mylist_folder"

    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    dt          = models.DateTimeField(verbose_name="作成日",default=timezone.now)
    title       = models.CharField(verbose_name="フォルダタイトル",max_length=50)
    description = models.CharField(verbose_name="フォルダ説明文",max_length=300)

    user        = models.ForeignKey(settings.AUTH_USER_MODEL,verbose_name="フォルダ所有者",on_delete=models.CASCADE)

    public      = models.BooleanField(verbose_name="フォルダ公開設定",default=False)
    search      = models.BooleanField(verbose_name="検索表示設定",default=False)

    def __str__(self):
        return self.title


#TODO:マイリストはマイリストフォルダに保存する。マイリストボタンを押した時、自動的に未分類マイリストフォルダに保存。マイリストフォルダは公開可能。
#フォルダ指定はNull可能。後で仕分ける方式
class VideoMyList(models.Model):

    class Meta:
        db_table    = "video_mylist"

    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    dt          = models.DateTimeField(verbose_name="登録日時",default=timezone.now)

    folder      = models.ForeignKey(VideoMyListFolder,verbose_name="所属フォルダ",on_delete=models.CASCADE,null=True,blank=True)
    target      = models.ForeignKey(Video,verbose_name="マイリスト動画",on_delete=models.CASCADE)
    user        = models.ForeignKey(settings.AUTH_USER_MODEL,verbose_name="登録したユーザー",on_delete=models.CASCADE)


    def __str__(self):
        return self.target.title

    
class VideoGood(models.Model):

    class Meta:
        db_table    = "video_good"

    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    dt          = models.DateTimeField(verbose_name="評価日時",default=timezone.now)
    target      = models.ForeignKey(Video,verbose_name="対象動画",on_delete=models.CASCADE)
    user        = models.ForeignKey(settings.AUTH_USER_MODEL,verbose_name="高評価したユーザー",on_delete=models.CASCADE)

    def __str__(self):
        return self.target.title

class VideoBad(models.Model):

    class Meta:
        db_table    = "video_bad"

    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    dt          = models.DateTimeField(verbose_name="評価日時",default=timezone.now)
    target      = models.ForeignKey(Video,verbose_name="対象動画",on_delete=models.CASCADE)
    user        = models.ForeignKey(settings.AUTH_USER_MODEL,verbose_name="低評価したユーザー",on_delete=models.CASCADE)

    def __str__(self):
        return self.target.title


#MEMO:ElementTubeにおけるNotifyとNewsの違い
"""
■Notify
【概要】
・通知の原本を作り、送信先を指定し、複写することで発信する
・特定のユーザー、あるいは全員に対して情報を発信できる
・既読判定機能がある
・未ログインユーザーは見れない
・後から新規作成されたアカウントには自動で情報発信されない

【用途】
・ユーザーが投稿した動画にコメントが投稿された、マイリストが一定数を超えた場合などの通知
・一部のユーザーだけに向けたキャンペーンなど
・一部ユーザーだけのキャンペーンの既読状況をチェックして、今後続けるか否か判断。

■News
【概要】
・トップページのカルーセルに一部情報が発信される
・カルーセルのリンククリックでNews個別ページに移動。詳細確認が可能
・未ログインユーザーも含め全員が見れる

【用途】
・全員に対して向けたキャンペーンなど(会員登録の促進、有料会員登録の促進など)
・未ログインユーザーでも確認必要なサイトメンテナンス情報など
・サイトに実装された新機能の解説など
"""

class NotifyCategory(models.Model):

    class Meta:
        db_table    = "notify_category"

    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name        = models.CharField(verbose_name="通知カテゴリ名",max_length=10)

    def __str__(self):
        return self.name

class Notify(models.Model):

    class Meta:
        db_table    = "notify"

    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    category    = models.ForeignKey(NotifyCategory,verbose_name="通知カテゴリ",on_delete=models.CASCADE,null=True)
    dt          = models.DateTimeField(verbose_name="通知作成日時",default=timezone.now)
    title       = models.CharField(verbose_name="通知タイトル",max_length=200)
    content     = models.CharField(verbose_name="通知内容",max_length=2000)
    target      = models.ManyToManyField(settings.AUTH_USER_MODEL,verbose_name="通知対象のユーザー",through="NotifyTarget",through_fields=("notify","user"))

    def __str__(self):
        return self.title

class NotifyTarget(models.Model):

    #下記で、組み合わせのユニークが実現できる。
    #https://stackoverflow.com/questions/2201598/how-to-define-two-fields-unique-as-couple

    class Meta:
        db_table        = "notify_target"
        unique_together = ("user","notify")

    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    dt          = models.DateTimeField(verbose_name="通知日時",default=timezone.now)
    notify      = models.ForeignKey(Notify,verbose_name="通知",on_delete=models.CASCADE)
    user        = models.ForeignKey(settings.AUTH_USER_MODEL,verbose_name="通知対象",on_delete=models.CASCADE)
    read        = models.BooleanField(verbose_name="既読",default=False)



#一般会員も見れる運営からの通知(ニュース)
#主に新機能追加時の解説やメンテナンス等の事前連絡、重要な通知等に使う。トップページなどにカルーセルで表示され、リンククリックでニュースページに飛ぶ。
#Notifyユーザーのフォローやコメント、マイリストの通知などに使うことで差別化。
class NewsCategory(models.Model):

    class Meta:
        db_table    = "news_category"

    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name        = models.CharField(verbose_name="ニュースカテゴリ",max_length=20)

    def __str__(self):
        return self.name

#TODO:ニュースの原稿はいずれマークダウン記法ができるよう配慮する予定。画像の挿入も。
class News(models.Model):

    class Meta:
        db_table    = "news"

    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    dt          = models.DateTimeField(verbose_name="作成日時",default=timezone.now)
    start_date  = models.DateField(verbose_name="カルーセル掲示期間(開始日)")
    end_date    = models.DateField(verbose_name="カルーセル掲示期間(終了日)")
    category    = models.ForeignKey(NewsCategory, verbose_name="ニュースカテゴリ", on_delete=models.PROTECT) 
    title       = models.CharField(verbose_name="ニュースタイトル",max_length=200)
    content     = models.CharField(verbose_name="ニュース内容",max_length=2000)

    def __str__(self):
        return self.title


#TODO:ヘルプにQAモデルとお問い合わせモデル(フォーム)を一緒くたに配置する。
class Faq(models.Model):

    class Meta:
        db_table    = "faq"

    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question    = models.CharField(verbose_name="質問",max_length=500)
    answer      = models.CharField(verbose_name="回答",max_length=500)

class Contact(models.Model):

    class Meta:
        db_table    = "contact"

    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    dt          = models.DateTimeField(verbose_name="問い合わせ日時",default=timezone.now)
    content     = models.CharField(verbose_name="お問い合わせ内容",max_length=1000)
    user        = models.ForeignKey(settings.AUTH_USER_MODEL,verbose_name="お問い合わせしたユーザー",on_delete=models.CASCADE,null=True,blank=True)
    ip          = models.GenericIPAddressField(verbose_name="お問い合わせした端末のIPアドレス")


#TODO:古いアクティビティがそのままになる問題あり。saveメソッドではみ出た部分を削除するかadminからアクションを追加するべき
class Activity(models.Model):

    class Meta:
        db_table    = "activity"

    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    date        = models.DateField(verbose_name="実行日",default=datetime.date.today)
    user        = models.ForeignKey(settings.AUTH_USER_MODEL,verbose_name="実行したユーザー",on_delete=models.CASCADE,null=True,blank=True)
    target      = models.ForeignKey(Video,verbose_name="対象動画",on_delete=models.CASCADE)
    category    = models.ForeignKey(VideoCategory,verbose_name="実行時の動画カテゴリ",on_delete=models.PROTECT)

    play        = models.IntegerField(verbose_name="再生点")
    mylist      = models.IntegerField(verbose_name="マイリスト点")
    good        = models.IntegerField(verbose_name="良いね点")
    bad         = models.IntegerField(verbose_name="悪いね点")
    comment     = models.IntegerField(verbose_name="コメント点")


class Config(models.Model):

    #https://docs.djangoproject.com/en/3.2/topics/db/examples/one_to_one/

    user            = models.OneToOneField(settings.AUTH_USER_MODEL,verbose_name="設定したユーザー",on_delete=models.CASCADE,primary_key=True)
    appear_news     = models.BooleanField(verbose_name="ニュースを表示",default=False)
    search_amount   = models.IntegerField(verbose_name="検索表示件数",default=10,validators=[MinValueValidator(10),MaxValueValidator(100)]) 



