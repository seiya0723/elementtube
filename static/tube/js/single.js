window.addEventListener("load" , function (){

    $("#single_video_comments_submit").on("click",function(){ comments_submit(); });
    $("#single_video_comments_textarea").on("keydown", function(e) { if( e.keyCode === 13 && e.shiftKey ) { comments_submit(); } });

    single_video_comments_form_initialize();

    $(document).on("click",".rating_good",function(){ rate_submit(true); });
    $(document).on("click",".rating_bad",function(){ rate_submit(false); });

    $(document).on("click","#mylist_submit",function(){ mylist_submit(); });


    $(document).on("click",".comment_page",function(){ get_comment_page( $(this).val()); });

    const video   = document.querySelector("video");
    video.addEventListener("volumechange",(event) => {
        document.cookie = "volume=" + decodeURIComponent(event.target.volume) + ";Path=/single;SameSite=strict";
    });
 
    //音量セットはvideo_initialize()にて
    //set_video_volume();


    video_initialize();


});


//Cookieから音量取得
function get_video_volume(){

    let cookies         = document.cookie;
    console.log(cookies);

    let cookiesArray    = cookies.split(';');
    let volume          = 0;

    for(let c of cookiesArray) {
        console.log(c);

        let cArray = c.split('=');
        if( cArray[0] === "volume"){
            volume  = Number(cArray[1]);
            console.log(volume);
            break;
        }
    }

    return volume;
}



//videoタグのコントローラ等の初期化処理
function video_initialize(){


    //#video-jsを{}内の設定で初期化、返り値のオブジェクトをplayerとする。
    let player  = videojs( 'video-js',{
        //コントロール表示、アクセスしたら自動再生、事前ロードする(一部ブラウザではできない)
        controls: true,
        //autoplay: true,
        preload: 'auto',
        
        //TODO:これは？
        networkState:2,
        seeking:true,
        liveui:true,
        
        fill:false,
        responsive: true,

        //再生速度の設定
        playbackRates: [ 0.25, 0.5, 1, 1.5, 2, 4,],


        //ローディングの表示
        LoadingSpinner:true,

        //音量は縦に表示
        controlBar: {
            volumePanel: { inline: false },
        }
    });
    
    //Cookieに格納されている音量の値をセットする。
    let v   = get_video_volume();
    player.volume(v);


    //生成したvideo.jsのオブジェクトに対して、イベントリスナの設定ができる。トリガーはvideoタグのものと同様
    player.on("loadstart",function(){ console.log("start"); });
    player.on("volumechange",function(){ console.log("音量が変わった"); });
    player.on("ended",function(){ console.log("end"); });


    //video.jsのオブジェクトにはいくらかメソッドがあるので、引数に#video-jsを指定することで追加の処理を実行できる
    //例:特定キーを押したら発動するイベントリスナを定義、動画をミュートする、次のトラックに行くなど
    /*
    let test    = videojs('video-js');
    test.volume(0.4);
    */


    player.addClass('vjs-matrix');
}

//videoタグに対しての音量セット方法(旧式) 
function set_video_volume(){
    let volume      = get_video_volume();
    const video     = document.querySelector("video");
    video.volume    = volume;
}

function comments_submit(){

    let form_elem   = "#single_video_comments_form";

    let data    = new FormData( $(form_elem).get(0) );
    let url     = $(form_elem).prop("action");
    let method  = $(form_elem).prop("method");

    for (let v of data.entries() ){ console.log(v); }

    $.ajax({
        url: url,
        type: method,
        data: data,
        processData: false,
        contentType: false,
        dataType: 'json'
    }).done( function(data, status, xhr ) { 

        if (data.error){
            $("#comments_message").addClass("upload_message_error");
            $("#comments_message").removeClass("upload_message_success");
        }
        else{
            $("#comments_message").addClass("upload_message_success");
            $("#comments_message").removeClass("upload_message_error");
            single_video_comments_form_initialize();

            $("#video_comments_area").html(data.content);
        }

        $("#comments_message").text(data.message)

    }).fail( function(xhr, status, error) {
        console.log(status + ":" + error );
    });

}
function single_video_comments_form_initialize() {
    $("[name='content']").val("");
}

function rate_submit(rate){

    console.log(rate);


    let form_elem   = ".single_video_rating_content";

    let data    = JSON.stringify({ "flag":rate });
    let url     = $(form_elem).prop("action");
    let method  = "PATCH";

    $.ajax({
        url: url,
        type: method,
        contentType : 'application/json; charset=utf-8',
        enctype     : "multipart/form-data",
        data: data,
    }).done( function(data, status, xhr ) { 

        if (data.error){
        }
        else{
            $("#single_video_rating_area").html(data.content);
        }

    }).fail( function(xhr, status, error) {
        console.log(status + ":" + error );
    });


}

function mylist_submit(id){

    let form_elem   = "#mylist_form_area";

    let data    = new FormData( $(form_elem).get(0) );
    let url     = $(form_elem).prop("action");
    let method  = $(form_elem).prop("method");

    for (let v of data.entries() ){ console.log(v); }

    $.ajax({
        url: url,
        type: method,
        data: data,
        processData: false,
        contentType: false,
        dataType: 'json'
    }).done( function(data, status, xhr ) { 

        if (data.error){
        }
        else{
            $("#single_video_rating_area").html(data.content);
        }

        /*
        if (data.error){
            $("#mylist_message").addClass("upload_message_error");
            $("#mylist_message").removeClass("upload_message_success");
        }
        else{
            $("#mylist_message").addClass("upload_message_success");
            $("#mylist_message").removeClass("upload_message_error");
        }

        $("#mylist_message").text(data.message)
        */

        //console.log(data);

    }).fail( function(xhr, status, error) {
        console.log(status + ":" + error );
    });

}


//コメントのページ移動
function get_comment_page(page){

    if (!(page)){ return false; }

    let form_elem   = "#comment_pagination_area";

    let url     = $(form_elem).prop("action") + "?page=" + page;
    let method  = $(form_elem).prop("method");

    console.log(url);

    $.ajax({
        url: url,
        type: "GET",
        dataType: 'json'
    }).done( function(data, status, xhr ) { 

        if (data.error){
            console.log("error");
        }
        else{
            $("#video_comments_area").html(data.content);
            $(".single_video_comments").animate({scrollTop:0},100);
        }
    }).fail( function(xhr, status, error) {
        console.log(status + ":" + error );
    });

}

