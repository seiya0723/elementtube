from django.contrib import admin
from .models import ( Video,VideoView,VideoComment,VideoCategory,
                    VideoMyList,VideoMyListFolder,VideoHistory,Notify,NotifyTarget,
                    NotifyCategory,Activity,NewsCategory,News,Config,Faq )
from .forms import NotifyAdminForm,NotifyTargetAdminForm,NewsAdminForm
from users.models import CustomUser

from django.utils.html import format_html


class NotifyAdmin(admin.ModelAdmin):

    list_display    = [ "category","dt","title","content" ]
    form            = NotifyAdminForm

    actions         = [ "all_notify","change_read","change_not_read" ]


    #選択した通知を全員に通知するアクション。
    def all_notify(self, request, queryset):
        
        #特定の条件に一致するユーザーに対して通知を送りたい場合は、下記をfilterに書き換え
        users       = list(CustomUser.objects.all().values_list("id",flat=True))

        for q in queryset:
            for user in users:
                formset = NotifyTargetAdminForm( { "notify":q.id,"user":user } )

                if formset.is_valid():
                    formset.save()

    all_notify.short_description    = "チェックした通知内容を全員に通知する"


    def change_read(self, request, queryset):
        id_list     = list(queryset.values_list("id",flat=True))
        notifies    = NotifyTarget.objects.filter(notify__in=id_list)

        for n in notifies:
            n.read  = True
            n.save()

    change_read.short_description       = "チェックした通知を全て既読化"

    def change_not_read(self, request, queryset):
        id_list     = list(queryset.values_list("id",flat=True))
        notifies    = NotifyTarget.objects.filter(notify__in=id_list)

        for n in notifies:
            n.read  = False
            n.save()

    change_not_read.short_description   = "チェックした通知を全て未読化"

    

class NotifyTargetAdmin(admin.ModelAdmin):

    list_display    = [ "notify","user","read" ]
    actions         = [ "change_read","change_not_read" ]

    #チェックした通知とターゲットの組み合わせを未読化させる
    def change_not_read(self, request, queryset):
        id_list     = list(queryset.values_list("id",flat=True))
        notifies    = NotifyTarget.objects.filter(id__in=id_list)

        for n in notifies:
            n.read  = False
            n.save()

    change_not_read.short_description   = "チェックした通知ターゲットを未読化"

    def change_read(self, request, queryset):
        id_list     = list(queryset.values_list("id",flat=True))
        notifies    = NotifyTarget.objects.filter(id__in=id_list)

        for n in notifies:
            n.read  = True
            n.save()

    change_read.short_description       = "チェックした通知ターゲットを既読化"

class NotifyCategoryAdmin(admin.ModelAdmin):
    list_display    = [ "name" ]


class VideoViewAdmin(admin.ModelAdmin):
    list_display    = [ "date","target","user","ip" ]


class NewsAdmin(admin.ModelAdmin):
    list_display    = [ "dt","start_date","end_date","category","title","content" ]
    form            = NewsAdminForm

class ActivityAdmin(admin.ModelAdmin):
    list_display    = [ "date","user","target","category","play","mylist","good","bad","comment" ]

class VideoAdmin(admin.ModelAdmin):
    list_display    = [ "category","dt","title","description","format_thumbnail","content" ]

    #画像のフィールドはimgタグで画像そのものを表示させる
    def format_thumbnail(self,obj):
        if obj.thumbnail:
            return format_html('<img src="{}" alt="画像" style="width:15rem">', obj.thumbnail.url)

    #画像を表示するときのラベル(photoのverbose_nameをそのまま参照している)
    format_thumbnail.short_description      = Video.thumbnail.field.verbose_name
    format_thumbnail.empty_value_display    = "画像なし"


admin.site.register(Video,VideoAdmin)
admin.site.register(VideoView,VideoViewAdmin)
admin.site.register(VideoComment)
admin.site.register(VideoCategory)
admin.site.register(VideoMyList)
admin.site.register(VideoMyListFolder)
admin.site.register(VideoHistory)
admin.site.register(Notify,NotifyAdmin)
admin.site.register(NotifyTarget,NotifyTargetAdmin)
admin.site.register(NotifyCategory,NotifyCategoryAdmin)
admin.site.register(NewsCategory)
admin.site.register(News,NewsAdmin)
admin.site.register(Activity,ActivityAdmin)
admin.site.register(Config)
admin.site.register(Faq)

