from django.urls import path
from . import views

app_name    = "tube"
urlpatterns = [ 

    #トップページ表示、キーワード検索、ページ移動
    path('', views.index, name="index"),

    #検索ページ
    path('search/', views.search, name="search"),

    #単一動画表示とコメント投稿、評価等
    path('single/<uuid:video_pk>/', views.single, name="single"),
    path('single_mod/<uuid:video_pk>/', views.single_mod, name="single_mod"),

    ##ランキングページ。DBからデータ抜き取って表示するだけ。GET文だけ
    path('rank/', views.rank, name="rank"),

    # 以下認証済みユーザー専用
    path('mypage/', views.mypage, name="mypage"),

    path('history/', views.history, name="history"),
    path('history_page/', views.history_page, name="history_page"),

    path('recommend/', views.recommend, name="recommend"),
    path('notify/', views.notify, name="notify"),

    #マイリストトップページではフォルダの一覧のリンクを表示させる。
    path('mylist/', views.mylist, name="mylist"),
    #GET:フォルダ一覧表示とページ移動
    #POST:マイリスト登録
    #DELETE:マイリストの削除(単体・複数)
    
    #フォルダの新規作成のみ受付
    path('mylist_folder/', views.mylist_folder, name="mylist_folder"),
    #GET:指定なしの場合、未分類のフォルダを表示させる
    #POST:フォルダ新規作成

    #フォルダ内のマイリストの表示、単体フォルダに対する削除、ページ移動
    path('mylist_folder/<uuid:folder_pk>/', views.mylist_folder, name="mylist_folder_single"),
    #GET:フォルダの中身表示・ページ移動←この部分だけフォルダの所有者でない一般ユーザーも閲覧可(ただし公開設定している場合に限られる。編集機能は所有者以外は隠す。ビューも所有者以外の操作は受け付けない。)
    #PUT:フォルダの説明文・タイトルなどの編集
    #DELETE:フォルダの削除
    #PATCH:マイリストのフォルダ移動(単体・複数)

    path('upload/', views.upload, name="upload"),
    path('config/', views.config, name="config"),

    #誰でも見ることができる
    path('news/', views.news, name="news"),
    path('news/<uuid:news_pk>/', views.news, name="news_single"),
    path('help/', views.help, name="help"),
    path('rule/', views.rule, name="rule"),


]
