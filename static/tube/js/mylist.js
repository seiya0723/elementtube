window.addEventListener("load" , function (){
    
    $("#mylist_multi_chk").prop("checked",false);

    $(".mylist_tab_label").on( "click", function(){ 
        $("#mylist_multi_chk").prop("checked",false);
        multi_hide();
    });

    $("#mylist_multi_chk").on("change", function(){
        if ( $(this).prop("checked") ){ multi_show(); }
        else{ multi_hide(); }
    });

    //TODO:移動する時、削除する時にモーダルダイアログを表示させる。移動先の指定、削除の確認など
    $(".mylist_multi_delete").on( "click", function(){ mylist_multi_delete(); });
    $(".mylist_multi_move").on( "click", function(){ mylist_multi_move(); });
    
    $(".mylist_delete_button").on("click", function(){ mylist_delete_send( [$(this).val()] ); });
    $(".mylist_folder_delete_button").on("click", function(){ mylist_folder_delete_send( $(this).val() ); });

    $("#mylist_folder_edit_submit").on("click",function(){ mylist_folder_edit_send(); });

});
function multi_show(){
    $(".delete_mylist_chk").prop("checked",false);
    $(".delete_mylist_chk").css({"display":"block"});
    $(".large_content_inner_cover").css({"display":"block"});
}
function multi_hide(){
    $(".delete_mylist_chk").css({"display":"none"});
    $(".large_content_inner_cover").css({"display":"none"});
}

function mylist_multi_move(){
    console.log("複数選択移動");

    //ここでUUIDリストと移動先のマイリストフォルダのUUIDを入手、mylist_folder_move_sendを実行する。

    let id_list = [];
    $("[name='delete_mylist[]']:checked").each(function(){ id_list.push(this.value); });
    let target  = $("#mylist_multi_select_form").val();

    console.log(id_list);
    console.log(target);

    mylist_folder_move_send(target,id_list);
}
function mylist_multi_delete(){
    let id_list = [];
    $("[name='delete_mylist[]']:checked").each(function(){ id_list.push(this.value); });
    mylist_delete_send(id_list);
}

//マイリストの削除(単発・複数)
function mylist_delete_send(id_list){

    console.log(id_list);

    //UUIDのリストを送信する。
    $.ajax({
        url: PATH["mylist"],
        type: "DELETE",
        contentType : 'application/json; charset=utf-8',
        enctype     : "multipart/form-data",
        data        : JSON.stringify( { "id_list":id_list } ),
        dataType: 'json'
    }).done( function(data, status, xhr ) {

        console.log(data);
        window.location.replace("");
        
        //reloadはメディアの再読込がされるため、かえって負荷がかかる。
        //location.reload();


    }).fail( function(xhr, status, error) {
        console.log(xhr + ":" + status + ":" + error);
    });

}


//マイリストフォルダの編集
function mylist_folder_edit_send(){

    let form_elem   = "#mylist_folder_edit_form";
    let data        = new FormData( $(form_elem).get(0) );
    let url         = $(form_elem).prop("action");

    //searchもしくはpublicのチェックボックスがチェックされていなければoffを指定。
    const necessary = ["search","public"];
    let keys        = [];
    for (let k of data.keys()){ keys.push(k); }
    for (let n of necessary){
        if ( keys.indexOf(n) === -1 ){
            data.set(n,"off");
        }
    }

    $.ajax({
        url: url,
        type: "PUT",
        data: data,
        processData: false,
        contentType: false,
        dataType: 'json'
    }).done( function(data, status, xhr ) {
        console.log(data);
        if (!data.flag){
            window.location.replace("");
        }
    }).fail( function(xhr, status, error) {
        console.log(xhr + ":" + status + ":" + error);
    });
}

//マイリストフォルダの削除(単発削除)
function mylist_folder_delete_send(target){

    $.ajax({
        url: PATH["mylist_folder"]+target+"/",
        type: "DELETE",
        contentType : false,
        enctype     : false,
        dataType: 'json'
    }).done( function(data, status, xhr ) {
        console.log(data);
        if (!data.flag){
            window.location.replace("");
        }
    }).fail( function(xhr, status, error) {
        console.log(xhr + ":" + status + ":" + error);
    });
}


//マイリストのフォルダ移動
function mylist_folder_move_send(target,id_list){

    $.ajax({
        url: PATH["mylist_folder"]+target+"/",
        type: "PATCH",
        contentType : 'application/json; charset=utf-8',
        enctype     : "multipart/form-data",
        data        : JSON.stringify( { "id_list":id_list } ),
        dataType: 'json'
    }).done( function(data, status, xhr ) {

        console.log(data);
        if (!data.flag){
            window.location.replace("");
        }

    }).fail( function(xhr, status, error) {
        console.log(xhr + ":" + status + ":" + error);
    });
}

