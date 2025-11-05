var onloadCallback = function () {
    secret_string = grecaptcha.render(document.getElementById('g-recaptcha'), {
        'sitekey': '6Ld3E8oUAAAAAFdUlaYKg90dgr9cwC3WdPtwhHZ-'
    })
}


$(document).ready(function () {
    $("input[type=phone]").mask("+7(999)999-99-99");
    $('#furl').val(window.location.href);
    $(".form button").on('click', function () {
        var form_info = $("#formland").serializeArray()
        var userip = $("input[name=userip]").val()
        var getcaptcha = grecaptcha.getResponse(secret_string)
        // console.log(form_info)
        if ($('input[name="agree"]').attr('checked')
        && $('input[name=name]').val() != ""
			&& $('input[name=phone]').val() != ""
			&& $('input[name=email]').val() != ""
			&& $('textarea[name=messag]').val() != ""
            && $('select[name=region]').val() != "") {

            $.ajax({
                type: 'post',
                url: 'capcha.php',
                data: { getcaptcha, userip },
                cache: false,
                success: function (data) {
                    console.log(data)
                    if (data == 'success') {

                        console.log('gtag form sended')
                        $.ajax({
                            url: 'mail.php',
                            type: 'POST',
                            data: form_info,
                            success: function (enddata) {
                                console.log(enddata)
                                $(".success").show()
                                $(".form button").hide()
                            }
                        })
                    }
                },
                error: function (error) {
                    alert('error; ' + eval(error));
                }

            })
        }
        else {
            if ($(".form input[name=agree]").hasClass('empty') || !$(".form input[name=agree]").attr('checked'))
                $("span.error.agree").css('display', 'block')

                $(".form select").each(function () {
                    if (!$(this).val()) {
                        $(this).addClass('errorinput')
                    }
                })
                $(".form textarea").each(function () {
                    if (!$(this).val()) {
                        $(this).addClass('errorinput')
                    }
                })
                $(".form input").each(function () {
                    if (!$(this).val()) {
                        $(this).addClass('errorinput')
                    }
                    else {
                        if ($(this).attr('name') == 'email' && ($(this).val()).indexOf('@') < 0) { $("span.error." + $(this).attr('name') + "fil").css('display', 'block'); $(this).addClass('errorinput') }
                        $(this).removeClass('empty')
                    }
                })
        }
    })
})