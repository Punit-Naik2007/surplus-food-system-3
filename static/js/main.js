/**
 * Surplus Food Redistribution and Donation Management System
 * Client-Side Interactivity, Notifications, Modals & Live Search
 */

document.addEventListener('DOMContentLoaded', function () {
  // 1. Initialize Bootstrap Tooltips & Popovers
  const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
  tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl);
  });

  // 2. Generic Confirmation Modals/Prompts for Destructive Actions
  const confirmForms = document.querySelectorAll('form[data-confirm]');
  confirmForms.forEach(form => {
    form.addEventListener('submit', function (e) {
      const message = form.getAttribute('data-confirm') || 'Are you sure you want to proceed?';
      if (!confirm(message)) {
        e.preventDefault();
      }
    });
  });

  // 3. Dynamic Client-Side Search for Tables
  const tableSearchInput = document.getElementById('tableSearchInput');
  if (tableSearchInput) {
    tableSearchInput.addEventListener('input', function () {
      const filter = this.value.toLowerCase();
      const tableRows = document.querySelectorAll('.searchable-table tbody tr');
      tableRows.forEach(row => {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(filter) ? '' : 'none';
      });
    });
  }

  // 4. Quick Notification Read Handler
  const notifItems = document.querySelectorAll('.notification-item[data-notif-id]');
  notifItems.forEach(item => {
    item.addEventListener('click', function () {
      const notifId = this.getAttribute('data-notif-id');
      const isRead = this.getAttribute('data-read') === '1';
      if (!isRead && notifId) {
        fetch(`/notifications/${notifId}/read`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' }
        }).then(res => res.json()).then(data => {
          if (data.success) {
            item.classList.remove('bg-light');
            item.setAttribute('data-read', '1');
            const unreadBadge = document.getElementById('navbarUnreadBadge');
            if (unreadBadge) {
              let count = parseInt(unreadBadge.textContent, 10);
              if (count > 1) {
                unreadBadge.textContent = count - 1;
              } else {
                unreadBadge.remove();
              }
            }
          }
        }).catch(err => console.error('Error marking notification read:', err));
      }
    });
  });

  // 5. Auto-dismiss alerts after 5 seconds
  const autoDismissAlerts = document.querySelectorAll('.alert-dismissible');
  autoDismissAlerts.forEach(alert => {
    setTimeout(() => {
      const bsAlert = new bootstrap.Alert(alert);
      try { bsAlert.close(); } catch (e) {}
    }, 6000);
  });
});
