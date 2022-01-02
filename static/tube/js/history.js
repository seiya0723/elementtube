window.addEventListener("load" , function (){
    
    $("#history_multi_chk").prop("checked",false);

    $(".history_tab_label").on( "click", function(){ 
        $("#history_multi_chk").prop("checked",false);
        multi_hide();
    });

    $("#history_multi_chk").on("change", function(){
        if ( $(this).prop("checked") ){ multi_show(); }
        else{ multi_hide(); }
    });

    $(".history_multi_delete").on( "click", function(){ history_multi_delete(); });
    $(document).on("click",".history_delete_button", function(){ history_delete_send( [$(this).val()] ); });
    //$(".history_delete_button").on("click", function(){ history_delete_send( [$(this).val()] ); });

});
function multi_show(){
    $(".delete_history_chk").prop("checked",false);
    $(".delete_history_chk").css({"display":"block"});
    $(".large_content_inner_cover").css({"display":"block"});
}
function multi_hide(){
    $(".delete_history_chk").css({"display":"none"});
    $(".large_content_inner_cover").css({"display":"none"});
}

function history_multi_delete(){

    let id_list = [];
    $("[name='delete_history[]']:checked").each(function(){ id_list.push(this.value); });
    history_delete_send(id_list);
}
function history_delete_send(id_list){

    console.log(id_list);

    //UUIDのリストを送信する。
    $.ajax({
        url: "",
        type: "DELETE",
        contentType : 'application/json; charset=utf-8',
        enctype     : "multipart/form-data",
        data        : JSON.stringify( { "id_list":id_list } ),
        dataType: 'json'
    }).done( function(data, status, xhr ) {

        //console.log(data);
        //console.log(data["histories"]);
        //console.log(data["good_histories"]);
        //console.log(data["mylist_histories"]);
        //console.log(data["comment_histories"]);

        //TODO:タブの名前とデータの値を一緒にさせるには、どちらかに統一する。マイリストフォルダの場合はフォルダのUUIDで統一したほうが良いだろう。
        $("#history_tab_body_1").html(data["histories"]);
        $("#history_tab_body_2").html(data["good_histories"]);
        $("#history_tab_body_3").html(data["mylist_histories"]);
        $("#history_tab_body_4").html(data["comment_histories"]);

    }).fail( function(xhr, status, error) {
        console.log(xhr + ":" + status + ":" + error);
    });

}


