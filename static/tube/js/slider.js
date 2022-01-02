window.addEventListener("load" , function (){

    //クリックした時、scroll()を実行する。押された要素(this)とブーリアン値(NextとPrevを見分ける)を引数にする。
    $(".previous_button").on("click",function(){ scroll(this,false); });
    $(".next_button").on("click",    function(){ scroll(this,true); });

});

//scroll関数
function scroll(elem,next){

    /* クリックされた箇所のスクロールする要素を抜き取る */
    let target  = $(elem).siblings(".data_preview_area");

    let all_width       = target.get(0).scrollWidth;
    let single_width    = target.outerWidth();
    let position_width  = target.scrollLeft();

    //先頭、末端までスクロールしたら、それぞれ戻る、進むができないように(jQueryアニメーション遅延問題)
    if ( (next) && ( all_width > single_width + position_width ) ){
        target.animate({ scrollLeft:"+=" + String(single_width) } , 300);
    }
    else if ( (!next) && ( 0 < position_width ) ){
        target.animate({ scrollLeft:"-=" + String(single_width) } , 300);
    }

}

