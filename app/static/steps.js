// Step counter (D-2026-10-15-22). One step = one click by the investigator on a link, button or menu.
// Typing is not counted. Version 1.0 and 2.0 keep separate counts, so the same case can be run in both
// and compared on screen. Counts live in this browser only; nothing is sent to the server.
(function () {
  var ver = document.body.getAttribute('data-steps') || 'v2';
  var key = 'ub_steps_' + ver, mem = [];
  function load() { try { return JSON.parse(localStorage.getItem(key) || '[]'); } catch (e) { return mem; } }
  function save(a) { mem = a; try { localStorage.setItem(key, JSON.stringify(a)); } catch (e) {} }
  function other() { try { return JSON.parse(localStorage.getItem(ver === 'v1' ? 'ub_steps_v2' : 'ub_steps_v1') || '[]').length; } catch (e) { return null; } }

  var box = document.createElement('details');
  box.className = 'steps steps-' + ver;
  box.innerHTML = '<summary title="One step = one click (link, button or menu). Typing is not counted. Reset before each run.">' +
    '<span class="steps-v">' + (ver === 'v1' ? 'Version 1.0' : 'Version 2.0') + '</span> Steps <b></b></summary>' +
    '<div class="steps-pop"><ol></ol><p class="steps-cmp"></p><button type="button" class="steps-reset">Reset count</button></div>';
  document.body.appendChild(box);

  function paint() {
    var a = load();
    box.querySelector('b').textContent = a.length;
    box.querySelector('ol').innerHTML = a.map(function (s) {
      return '<li>' + s.replace(/[<>&]/g, function (c) { return { '<': '&lt;', '>': '&gt;', '&': '&amp;' }[c]; }) + '</li>';
    }).join('') || '<li class="none">No steps yet</li>';
    var o = other();
    box.querySelector('.steps-cmp').textContent = o === null ? '' : (ver === 'v1' ? 'Version 2.0' : 'Version 1.0') + ' last run: ' + o + ' steps';
  }
  paint();

  box.querySelector('.steps-reset').addEventListener('click', function (e) { e.stopPropagation(); save([]); paint(); });
  document.addEventListener('click', function (e) {
    if (box.contains(e.target)) return;
    var el = e.target.closest('a[href], button, summary, input[type=submit]');
    if (!el || el.closest('.topbar') || el.closest('.v1user')) return; // sound, user menu and sign-out are not work steps
    if (el.tagName === 'SUMMARY' && el.closest('details.help')) return; // "?" help popovers are not work steps
    var label = (el.getAttribute('aria-label') || el.textContent || el.value || '').replace(/\s+/g, ' ').trim().slice(0, 40) || el.tagName.toLowerCase();
    // A button on its own ("Search", "Escalate") says little in the list: add the screen it was pressed on.
    if (el.tagName !== 'A' && el.tagName !== 'SUMMARY') {
      var h = document.querySelector('main h1');
      var where = h ? h.textContent.replace(/\s+/g, ' ').split(':')[0].trim() : '';
      if (where && label.indexOf(where) < 0) label += ' (' + where + ')';
    }
    var a = load(); a.push(label); save(a); paint();
  }, true);
})();
