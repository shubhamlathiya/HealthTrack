document.addEventListener('DOMContentLoaded', function () {
    var calendarEl = document.getElementById('appointmentsCal');

    var calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'dayGridMonth',
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,timeGridDay,listWeek'
        },
        events: '/get-appointments',
        eventClick: function (info) {
            // Show appointment details in a modal
            $('#appointmentDetailsModal .modal-title').text('Appointment Details');
            $('#appointmentDetailsModal .modal-body').html(`
                <p><strong>Patient:</strong> ${info.event.title}</p>
                <p><strong>Time:</strong> ${info.event.start.toLocaleString()}</p>
                <p><strong>Reason:</strong> ${info.event.extendedProps.reason}</p>
                <p><strong>Status:</strong> ${info.event.extendedProps.status}</p>
                <div class="mt-3">
                    <button class="btn btn-primary btn-sm forward-btn" 
                            data-id="${info.event.id}">
                        Forward Appointment
                    </button>
                </div>
            `);
            $('#appointmentDetailsModal').modal('show');
        },
        eventContent: function (arg) {
            // Customize event display
            return {
                html: `
                    <div class="fc-event-main-frame">
                        <div class="fc-event-title-container">
                            <div class="fc-event-title fc-sticky">
                                <i class="ri-user-line me-1"></i>${arg.event.title}
                            </div>
                        </div>
                        <div class="fc-event-time">${arg.timeText}</div>
                    </div>
                `
            };
        }
    });

    calendar.render();
});