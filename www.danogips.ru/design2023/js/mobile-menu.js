$(document).ready(function(){
   /* Когда пользователь нажимает на кнопку,
   переключение между скрытием и отображением раскрывающегося содержимого */
   
   var menu = document.querySelector ("#menu");
   var mobile = document.querySelector ("#mobile");
   var mobi = document.querySelector ("#mobi");
   var mob = document.querySelector ("#mobile-menu");
    mobi.addEventListener ("click", function() {
       menu.classList.toggle("show");
       mob.classList.toggle("show-active");
       mobile.classList.toggle("mobile-active");
    });
   
   
  
    /*
   
   
      var margin = 0; // переменная для контроля докрутки
      $("a").click(function() { // тут пишите условия, для всех ссылок или для конкретных
         $("html, body").animate({
            scrollTop: $($(this).attr("href")).offset().top-margin+ "px" // .top+margin - ставьте минус, если хотите увеличить отступ
         }, {
            duration: 1600, // тут можно контролировать скорость
            easing: "swing"
         });
         return false;
      });
   */
   
   });

