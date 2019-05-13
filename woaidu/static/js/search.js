var listgroup = '<div class="list-group"></div>';
var query_status = 1;
function status_inc() { 
        query_status = query_status + 1;
        if(query_status > 0){$(".progress").hide();}
        else{$(".progress").show();}
} 
function status_des() { 
        query_status = query_status - 1;
        if(query_status > 0){$(".progress").hide();}
        else{$(".progress").show();}
}
function search_book(){
        $.ajax({
            url: "{% url 'woaidu:search' %}",
            type: "POST",
            dataType:'json',
            data: {"p": $("#search-url").val()},
            beforeSend:function(){status_des()},
            success: function (e) {
                console.log(e)
                if (e) {
                    console.log('123')
                    alert("加载完成...");
                }
                else {
                    console.log('456')
                }
            },
        });

}
$(document).ready(function(){


    if(query_status > 0){
    $(".progress").hide();
    }
    else{$(".progress").show();}
})
