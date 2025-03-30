$.sidebarMenu = function (menu) {
  var animationSpeed = 300;

  $(menu).on("click", "li a", function (e) {
    var $this = $(this);
    var checkElement = $this.next();

    if (checkElement.is(".treeview-menu") && checkElement.is(":visible")) {
      checkElement.slideUp(animationSpeed, function () {
        checkElement.removeClass("menu-open");
      });
      checkElement.parent("li").removeClass("active");
    }

    //If the menu is not visible
    else if (
      checkElement.is(".treeview-menu") &&
      !checkElement.is(":visible")
    ) {
      //Get the parent menu
      var parent = $this.parents("ul").first();
      //Close all open menus within the parent
      var ul = parent.find("ul:visible").slideUp(animationSpeed);
      //Remove the menu-open class from the parent
      ul.removeClass("menu-open");
      //Get the parent li
      var parent_li = $this.parent("li");

      //Open the target menu and add the menu-open class
      checkElement.slideDown(animationSpeed, function () {
        //Add the class active to the parent li
        checkElement.addClass("menu-open");
        parent.find("li.active").removeClass("active");
        parent_li.addClass("active");
      });
    }
    //if this isn't a link, prevent the page from being redirected
    if (checkElement.is(".treeview-menu")) {
      e.preventDefault();
    }
  });
};
$.sidebarMenu($(".sidebar-menu"));

// Custom Sidebar JS
jQuery(function ($) {
  //toggle sidebar
  $(".toggle-sidebar").on("click", function () {
    $(".page-wrapper").toggleClass("toggled");
  });

  // Pin sidebar on click
  $(".pin-sidebar").on("click", function () {
    if ($(".page-wrapper").hasClass("pinned")) {
      // unpin sidebar when hovered
      $(".page-wrapper").removeClass("pinned");
      $("#sidebar").unbind("hover");
    } else {
      $(".page-wrapper").addClass("pinned");
      $("#sidebar").on("mouseenter", function () {
        console.log("mouseenter");
        $(".page-wrapper").addClass("sidebar-hovered");
      });

      $("#sidebar").on("mouseleave", function () {
        console.log("mouseout");
        $(".page-wrapper").removeClass("sidebar-hovered");
      });
    }
  });

  // Pinned sidebar
  $(function () {
    if ($(".page-wrapper").hasClass("pinned")) {
      $("#sidebar")
        .on("mouseenter", function () {
          console.log("mouseenter");
          $(".page-wrapper").addClass("sidebar-hovered");
        })
        .on("mouseleave", function () {
          console.log("mouseleave");
          $(".page-wrapper").removeClass("sidebar-hovered");
        });
    }
  });

  // Toggle sidebar overlay
  $("#overlay").on("click", function () {
    $(".page-wrapper").toggleClass("toggled");
  });

  // Added by Srinu
  $(function () {
    // When the window is resized,
    $(window).resize(function () {
      // When the width and height meet your specific requirements or lower
      if ($(window).width() <= 768) {
        $(".page-wrapper").removeClass("pinned");
      }
    });
    // When the window is resized,
    $(window).resize(function () {
      // When the width and height meet your specific requirements or lower
      if ($(window).width() >= 768) {
        $(".page-wrapper").removeClass("toggled");
      }
    });
  });
});

// Date Picker Loading
$(document).ready(function () {
  // Simulate loading delay
  setTimeout(function () {
    var datepickerLoader = document.getElementById('datepicker-loader');
    var datepicker = document.getElementById('datepicker');
    if (datepickerLoader) {
      datepickerLoader.classList.add('d-none');
    }
    if (datepicker) {
      datepicker.classList.remove('d-none');
    }
  }, 2000); // Adjust the delay as needed
});

// Loading
$(function () {
  $("#loading-wrapper").fadeOut(3000);
});

$(function () {
  $(".day-sorting .btn").on("click", function () {
    $(".day-sorting .btn").removeClass("btn-primary");
    $(this).addClass("btn-primary");
  });
});

// Current Month
$(document).ready(function () {
  var monthNames = [
    "January", "February", "March", "April",
    "May", "June", "July", "August",
    "September", "October", "November", "December"
  ];
  var currentMonth = new Date().getMonth(); // 0-11 index
  $(".monthDisplay").text('In ' + monthNames[currentMonth]);
});

// Week Days Btn Select
$(document).ready(function () {
  $('.week-days a').click(function () {
    // Remove primary class from all links and add secondary
    $('.week-days a').removeClass('bg-primary text-white').addClass('bg-secondary-subtle');
    // Add primary class to the clicked link and remove secondary
    $(this).addClass('bg-primary text-white').removeClass('bg-secondary-subtle');
  });
});

// Week Days Btn Group
$(document).ready(function () {
  $('.week-days-btn-group .btn').click(function () {
    // Remove primary class from all links and add light
    $('.week-days-btn-group .btn').removeClass('btn-primary').addClass('btn-light');
    // Add primary class to the clicked link and remove light
    $(this).addClass('btn-primary').removeClass('btn-light');
  });
});

// Current Day
$(document).ready(function () {
  const today = new Date();
  const day = today.toLocaleString('default', { weekday: 'long' });
  const date = today.getDate();
  const dayElement = document.querySelector('.day');
  const dateElement = document.querySelector('.today-date');
  if (dayElement) {
    dayElement.textContent = day;
  }
  if (dateElement) {
    dateElement.textContent = date;
  }
});


/***********
***********
***********
  Bootstrap JS 
***********
***********
***********/

// Tooltip
var tooltipTriggerList = [].slice.call(
  document.querySelectorAll('[data-bs-toggle="tooltip"]')
);
var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
  return new bootstrap.Tooltip(tooltipTriggerEl);
});

// Popover
var popoverTriggerList = [].slice.call(
  document.querySelectorAll('[data-bs-toggle="popover"]')
);
var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
  return new bootstrap.Popover(popoverTriggerEl);
});
