/**
 * oscar_announcements — dismiss announcements without reloading the page.
 *
 * For each `.oa-announcement__dismiss-form`, the form submit is intercepted
 * and sent as an AJAX POST.  On success the announcement element is removed
 * from the DOM.  If JavaScript is disabled or the fetch fails, the form
 * submits normally (full-page POST → redirect back).
 *
 * Include this script once in your base template, e.g.::
 *
 *   <script src="{% static 'oscar_announcements/js/announcements.js' %}"></script>
 */
(function () {
    "use strict";

    function getCsrfToken() {
        var el = document.querySelector("[name=csrfmiddlewaretoken]");
        return el ? el.value : "";
    }

    function dismissAnnouncement(form) {
        var ann = form.closest(".oa-announcement");
        fetch(form.action, {
            method: "POST",
            headers: {
                "X-CSRFToken": getCsrfToken(),
                "X-Requested-With": "XMLHttpRequest",
            },
        })
            .then(function (resp) {
                if (resp.ok && ann) {
                    ann.remove();
                } else {
                    form.submit();
                }
            })
            .catch(function () {
                form.submit();
            });
    }

    document.addEventListener("DOMContentLoaded", function () {
        document
            .querySelectorAll(".oa-announcement__dismiss-form")
            .forEach(function (form) {
                form.addEventListener("submit", function (e) {
                    e.preventDefault();
                    dismissAnnouncement(form);
                });
            });
    });
}());
