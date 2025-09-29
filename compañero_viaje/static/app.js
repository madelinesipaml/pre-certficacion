// app.js - basic client-side enhancements

// Auto-hide flash messages
window.addEventListener('DOMContentLoaded', () => {
  // Flash auto-hide
  const flashes = document.querySelectorAll('.flash');
  if (flashes.length) setTimeout(() => flashes.forEach(f => f.style.display = 'none'), 4500);

  // Modal helpers
  const modalRoot = document.getElementById('modal-root');
  const modalTitle = document.getElementById('modal-title');
  const modalBody = document.getElementById('modal-body');
  const modalConfirm = document.getElementById('modal-confirm');
  const modalCancel = document.getElementById('modal-cancel');

  function openModal(title, bodyHtml){
    modalTitle.textContent = title;
    modalBody.innerHTML = bodyHtml;
    modalRoot.setAttribute('aria-hidden', 'false');
    modalConfirm.focus();
  }
  function closeModal(){
    modalRoot.setAttribute('aria-hidden', 'true');
  }

  modalCancel.addEventListener('click', closeModal);

  // Delete via modal + fetch + animation
  document.querySelectorAll('form[action][method="post"]').forEach(form => {
    if (form.action.includes('/trips/') && form.action.endsWith('/delete')) {
      form.addEventListener('submit', (e) => {
        e.preventDefault();
        const row = form.closest('tr');
        openModal('Confirmar eliminación', '<p>¿Deseas eliminar este viaje? Esta acción no se puede deshacer.</p>');
        const onConfirm = async () => {
          try {
            // submit form via fetch
            const resp = await fetch(form.action, { method: 'POST', headers: {'Accept':'text/html'} });
            if (resp.ok) {
              // animate row out then remove
              if (row){ row.classList.add('fade-out'); setTimeout(()=> row.remove(), 480); }
            } else {
              alert('Error al eliminar el viaje.');
            }
          } catch (err){
            alert('Error de red al eliminar.');
          } finally {
            closeModal();
            modalConfirm.removeEventListener('click', onConfirm);
          }
        };
        modalConfirm.addEventListener('click', onConfirm);
      });
    }
  });

  // register form validation: confirm password (modal)
  const reg = document.querySelector('form[action="/register"]');
  if (reg) {
    reg.addEventListener('submit', (e) => {
      const p = reg.querySelector('input[name="password"]');
      const c = reg.querySelector('input[name="confirm"]');
      if (p && c && p.value !== c.value) {
        e.preventDefault();
        openModal('Error', '<p>Las contraseñas no coinciden.</p>');
      }
    });
  }

  // new trip - validate dates (modal) + extra UX (confirm, dirty-check, shortcuts)
  const newTrip = document.querySelector('form[action="/trips/new"]');
  if (newTrip) {
    // find the submit button (could be <button> or <input>)
    const submitBtn = newTrip.querySelector('button[type="submit"], input[type="submit"]');

    // helper to check if form has user input (dirty)
    const isDirty = () => {
      const inputs = Array.from(newTrip.querySelectorAll('input, textarea'));
      return inputs.some(i => i.type !== 'hidden' && i.value && i.value.trim() !== '');
    };

    // Intercept 'Volver' links inside form actions to warn about unsaved changes
    const backLink = newTrip.querySelector('a[href="/"]');
    if (backLink) {
      backLink.addEventListener('click', (ev) => {
        if (isDirty()) {
          ev.preventDefault();
          openModal('Salir sin guardar', '<p>Tienes cambios sin guardar. ¿Deseas salir y perder los cambios?</p>');
          const onLeave = () => { window.location = backLink.href; };
          modalConfirm.addEventListener('click', onLeave, { once: true });
        }
      });
    }

    // Ctrl/Cmd+Enter shortcut to submit
    newTrip.addEventListener('keydown', (ev) => {
      if ((ev.ctrlKey || ev.metaKey) && ev.key === 'Enter') {
        ev.preventDefault();
        submitBtn && submitBtn.click();
      }
    });

    newTrip.addEventListener('submit', (e) => {
      const fi = newTrip.querySelector('input[name="fecha_inicio"]');
      const ff = newTrip.querySelector('input[name="fecha_fin"]');

      // date validation
      if (fi && ff) {
        if (ff.value < fi.value) {
          e.preventDefault();
          openModal('Error de fechas', '<p>La fecha de fin debe ser posterior o igual a la fecha de inicio.</p>');
          return;
        }
      }

      // confirmation before final submit
      if (!e.defaultPrevented) {
        e.preventDefault();
        openModal('Confirmar creación', '<p>¿Deseas crear este viaje ahora?</p>');

        const doSubmit = () => {
          try {
            if (submitBtn) {
              submitBtn.disabled = true;
              if (!submitBtn.querySelector('.spinner')) {
                const s = document.createElement('span');
                s.className = 'spinner';
                submitBtn.appendChild(s);
              }
            }
            modalConfirm.removeEventListener('click', doSubmit);
            closeModal();
            newTrip.submit(); // native submit
          } catch (err) {
            closeModal();
          }
        };

        modalConfirm.addEventListener('click', doSubmit, { once: true });
        // ensure cancel doesn't leak listeners
        modalCancel.addEventListener('click', function onCancel(){ modalConfirm.removeEventListener('click', doSubmit); modalCancel.removeEventListener('click', onCancel); }, { once: true});
      }
    });
  }
});

// Highlight newly created row if new_id is present in URL
(function highlightNewRow(){
  try{
    const params = new URLSearchParams(window.location.search);
    const newId = params.get('new_id');
    if (!newId) return;
    const row = document.querySelector(`tr[data-trip-id="${newId}"]`);
    if (row){
      row.classList.add('new-highlight');
      setTimeout(()=> row.classList.remove('new-highlight'), 2800);
      // remove query param
      params.delete('new_id');
      const newUrl = window.location.pathname + (params.toString() ? '?' + params.toString() : '');
      window.history.replaceState({}, '', newUrl);
    }
  }catch(e){/* ignore */}
})();
