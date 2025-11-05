$(document).ready(function(){
   /* Когда пользователь нажимает на кнопку,
   переключение между скрытием и отображением раскрывающегося содержимого */
   
   var menu = document.querySelector ("#menu");
   var mobile = document.querySelector ("#mobile");
   var overlay = document.querySelector (".header-overlay");
    mobile.addEventListener ("click", function() {
       menu.classList.toggle("show");
       overlay.classList.toggle("header-overlay__active");
       mobile.classList.toggle("mobile-active");
    });
   
    overlay.addEventListener ("click", function() {
      menu.classList.toggle("show");
   
      mobile.classList.toggle("mobile-active");
      overlay.classList.toggle("header-overlay__active");
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


   $(function() {
      var tab = $('.gid-tabs .gid-part > div'); 
      tab.hide().filter(':first').show(); 
      
      // Клики по вкладкам.
      $('.gid-tabs .gid-nav a').click(function(){
         tab.hide(); 
         tab.filter(this.hash).show(); 
         $('.gid-tabs .gid-nav a').removeClass('active');
         $(this).addClass('active');
         return false;
      }).filter(':first').click();
    
      // Клики по якорным ссылкам.
      $('.tabs-target').click(function(){
         $('.gid-tabs .gid-nav a[href=' + $(this).attr('href')+ ']').click();
      });
      
      // Отрытие вкладки из хеша URL
      if(window.location.hash){
         $('.gid-nav a[href=' + window.location.hash + ']').click();
         window.scrollTo(0, $("#" . window.location.hash).offset().top);
      }
   });