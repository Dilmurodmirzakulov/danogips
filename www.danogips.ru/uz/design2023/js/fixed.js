$(document).ready( function() {
    if ($('.header').width() >= 1) {
      $(function() {
         let header = $('.header');
         
        
         let hederHeight = header.height(); // calculate the height of the cap
          
         $(window).scroll(function() {
           if($(this).scrollTop() > 1) {
            header.addClass('header-fixed');
       
            
           } else {
            header.removeClass('header-fixed');
          
           }
       
         });
        });
    }

} );