/**
 * Created by Longy on 18.05.15.
 */
$( document ).ready(function() {
    // Handler for .ready() called.
    $( "#saveresult" ).click(function() {
        //Get filename
        var filename = $('#filename').val();

        //Check if filename is not empty
        if(filename){
            //Save result with the given filename
            $.ajax({
                type: "POST",
                data: JSON.stringify({content: $('#shared_widgets_NumberInput_2').val()}),
                contentType: "application/json; charset=utf-8",
                url: "/storage/api/v1.0/"+user_id+"/"+filename,
                success: function (response) {
                    if(response == "200"){
                        //Hide modal after successfully saving the result
                        $('#saveFileModal').modal('hide')
                    }
                },
                error: function (data) {
                    console.log("error in post request");
                }
            });
        }

    });
    $( "#loadresult" ).click(function() {
        $.ajax({
            type: "GET",
            contentType: "application/json; charset=utf-8",
            url: "/storage/api/v1.0/"+user_id+"/calculator",
            success: function (data) {
                alert("Result retrieved: " + data)
            },
            error: function (data) {
                console.log("error in get request");
            }
        });
    });
});