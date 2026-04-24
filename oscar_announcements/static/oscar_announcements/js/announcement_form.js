(function () {
    var startBtn = document.querySelector(".oa-clear-date[data-label-now]");
    var startField = startBtn ? document.getElementById(startBtn.dataset.target) : null;
    var startLabel = startBtn ? startBtn.querySelector(".oa-start-label") : null;

    function updateStartLabel() {
        if (!startField || !startLabel || !startBtn) return;
        var val = startField.value;
        if (!val) {
            startLabel.textContent = startBtn.dataset.labelNow;
            return;
        }
        var diffDays = Math.round((new Date(val) - new Date()) / 86400000);
        if (diffDays <= 0) {
            startLabel.textContent = startBtn.dataset.labelNow;
        } else if (diffDays === 1) {
            startLabel.textContent = startBtn.dataset.labelDay;
        } else {
            startLabel.textContent = startBtn.dataset.labelDaysPrefix + " " + diffDays + " " + startBtn.dataset.labelDaysSuffix;
        }
    }

    document.querySelectorAll(".oa-clear-date").forEach(function (btn) {
        btn.addEventListener("click", function () {
            var field = document.getElementById(btn.dataset.target);
            if (field) {
                field.value = "";
                updateStartLabel();
            }
        });
    });

    if (startField) {
        startField.addEventListener("change", updateStartLabel);
        updateStartLabel();
    }
}());
