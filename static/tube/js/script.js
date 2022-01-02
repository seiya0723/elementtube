window.addEventListener("load" , function (){
    news_area();
});
function news_area(){

    //スライド領域、子要素を手に入れる。
    let slide_area  = $("#news_slide_area");
    let children    = slide_area.children();

    //1つめの子要素(ニュース)をクローンして最後尾に追加する
    slide_area.append(children.first().clone());

    var amount      = children.length + 1;
    var count       = 0;

    //要素の幅(px)を抜き取りずらす。(これでレスポンシブに対応できる。)
    function slide(){
        count++;

        //TIPS:なぜ、ループごとにsingleを定義するのか？←スマホで画面を縦から横に動かされた時、必ずずれるから。
        //TODO:縦から横に変わった時、一瞬空白ができるから、ブラウザ幅変更時に発動するイベントを追加したほうが良いかも。
        let single      = children.first().outerWidth();
        var slide_range = String(-(count%amount)*single) + "px";

        //最後の要素(コピーの要素)になったらすぐに最初に戻す。
        $("#news_slide_area").animate({"left":slide_range}, 500 , function() { endcheck(); } );
    }   
    function endcheck(){
        if (count%amount === amount-1){
            $("#news_slide_area").css({"left":"0"});
            count   = 0;
        }
    }   

    setInterval(slide, 5000);
}
