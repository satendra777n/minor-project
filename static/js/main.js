document.addEventListener("DOMContentLoaded", function () {
  var form = document.getElementById("assessment-form");
  if (form) {
    form.addEventListener("submit", function (e) {
      var groups = form.querySelectorAll("[data-question]");
      var unanswered = 0;
      groups.forEach(function (g) {
        var name = g.getAttribute("data-question");
        if (!form.querySelector('input[name="' + name + '"]:checked')) {
          unanswered++;
        }
      });
      if (unanswered > 0) {
        e.preventDefault();
        alert("Please answer all " + groups.length + " questions before submitting (" + unanswered + " left).");
      }
    });
  }
});
