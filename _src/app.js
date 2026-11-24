/* Detailed By Jarrad: menu picks, instant estimate, photo dropbox and the quote form.
   No dependencies, and no network calls until a request is sent. */
(function () {
  'use strict';

  var config = window.SITE_CONFIG || {};
  var root = document.documentElement;
  var picked = [];
  var photos = [];
  var photoLimit = config.photoLimit || 6;
  var maxSide = 1600;

  var prices = config.services || {};
  var vehicles = config.vehicles || [];
  var dirts = config.dirts || [];
  var currency = config.currency || '$';

  var menuButtons = Array.prototype.slice.call(document.querySelectorAll('[data-service]'));
  var countButton = document.getElementById('quote-count');
  var chosenBox = document.getElementById('chosen');
  var form = document.getElementById('quote-form');
  var servicesField = document.getElementById('f-services');
  var vehicleField = document.getElementById('f-vehicle');
  var dirtField = document.getElementById('f-dirt');
  var messageField = document.getElementById('f-message');
  var statusLine = document.getElementById('form-status');
  var submitButton = form.querySelector('button[type="submit"]');
  var estFigure = document.getElementById('est-figure');
  var estNote = document.getElementById('est-note');
  var dropzone = document.getElementById('dropzone');
  var fileInput = document.getElementById('f-photos');
  var pickButton = document.getElementById('photo-pick');
  var photoList = document.getElementById('photos');
  var photoStatus = document.getElementById('photo-status');
  var drawer = document.getElementById('quote-list');
  var drawerItems = document.getElementById('ql-items');
  var drawerEmpty = document.getElementById('ql-empty');
  var drawerGo = document.getElementById('ql-go');
  var quoteSection = document.getElementById('quote');

  function byId(list, id) {
    for (var i = 0; i < list.length; i++) {
      if (list[i].id === id) {
        return list[i];
      }
    }
    return null;
  }

  function nameFor(id) {
    for (var i = 0; i < menuButtons.length; i++) {
      if (menuButtons[i].getAttribute('data-service') === id) {
        return menuButtons[i].getAttribute('data-name');
      }
    }
    return id;
  }

  function selectedLabel(select) {
    var option = select.options[select.selectedIndex];
    return option ? option.text : '';
  }

  function focusMenuButton(id) {
    menuButtons.forEach(function (button) {
      if (button.getAttribute('data-service') === id) {
        button.focus();
      }
    });
  }

  function isPicked(id) {
    return picked.indexOf(id) !== -1;
  }

  function pick(id) {
    if (!isPicked(id)) {
      picked.push(id);
    }
    render();
  }

  function unpick(id) {
    picked = picked.filter(function (item) {
      return item !== id;
    });
    render();
  }

  /* Estimate. A price stays pending (null) until Jarrad sets it in data.json. */

  function money(amount) {
    return currency + Math.round(amount).toLocaleString('en-AU');
  }

  function estimate() {
    if (picked.length === 0) {
      return { kind: 'empty' };
    }
    var vehicle = byId(vehicles, vehicleField.value);
    var dirt = byId(dirts, dirtField.value);
    var pending = !vehicle || typeof vehicle.multiplier !== 'number' ||
      !dirt || typeof dirt.extra !== 'number';
    var subtotal = 0;
    picked.forEach(function (id) {
      var price = prices[id];
      if (typeof price === 'number') {
        subtotal += price;
      } else {
        pending = true;
      }
    });
    if (pending) {
      return { kind: 'pending' };
    }
    return {
      kind: 'price',
      total: subtotal * vehicle.multiplier * (1 + dirt.extra / 100)
    };
  }

  function estimateSummary() {
    var state = estimate();
    if (state.kind === 'price') {
      return money(state.total) + ' (estimate, final price confirmed by ' + config.owner + ')';
    }
    return state.kind === 'pending' ? 'To be confirmed by ' + config.owner : 'No services chosen';
  }

  function renderEstimate() {
    var state = estimate();
    estFigure.classList.toggle('is-pending', state.kind !== 'price');
    if (state.kind === 'empty') {
      estFigure.textContent = 'Choose a service';
      estNote.textContent = 'Pick at least one service from the menu. Your estimate updates as you choose.';
    } else if (state.kind === 'pending') {
      estFigure.textContent = 'To be confirmed';
      estNote.textContent = config.owner + ' confirms your exact price after he reviews your photos.';
    } else {
      estFigure.textContent = money(state.total);
      estNote.textContent = 'Estimated total. ' + config.owner + ' confirms the final price after he reviews your photos.';
    }
  }

  /* Drawer and header count */

  function removeButton(id) {
    var button = document.createElement('button');
    button.type = 'button';
    button.className = 'chip-remove';
    button.textContent = 'Remove';
    button.setAttribute('aria-label', 'Remove ' + nameFor(id) + ' from quote');
    button.addEventListener('click', function () {
      var inDrawer = drawer.open;
      unpick(id);
      if (inDrawer) {
        drawerGo.focus();
      } else {
        focusMenuButton(id);
      }
    });
    return button;
  }

  function render() {
    menuButtons.forEach(function (button) {
      var on = isPicked(button.getAttribute('data-service'));
      button.setAttribute('aria-pressed', on ? 'true' : 'false');
      button.textContent = on ? 'Remove from quote' : 'Add to quote';
    });

    countButton.textContent = 'Quote (' + picked.length + ')';

    drawerItems.textContent = '';
    picked.forEach(function (id) {
      var row = document.createElement('li');
      var label = document.createElement('span');
      label.textContent = nameFor(id);
      row.appendChild(label);
      row.appendChild(removeButton(id));
      drawerItems.appendChild(row);
    });
    drawerItems.hidden = picked.length === 0;
    drawerEmpty.hidden = picked.length > 0;

    chosenBox.textContent = '';
    if (picked.length === 0) {
      var empty = document.createElement('p');
      empty.className = 'chosen-empty';
      empty.textContent = 'No services chosen yet. Add them from the menu above.';
      chosenBox.appendChild(empty);
    } else {
      picked.forEach(function (id) {
        var chip = document.createElement('span');
        chip.className = 'chip';
        chip.appendChild(document.createTextNode(nameFor(id)));
        chip.appendChild(removeButton(id));
        chosenBox.appendChild(chip);
      });
    }

    servicesField.value = picked.map(nameFor).join(', ');
    renderEstimate();
  }

  menuButtons.forEach(function (button) {
    button.addEventListener('click', function () {
      var id = button.getAttribute('data-service');
      if (isPicked(id)) {
        unpick(id);
      } else {
        pick(id);
      }
    });
  });

  vehicleField.addEventListener('change', renderEstimate);
  dirtField.addEventListener('change', renderEstimate);

  countButton.addEventListener('click', function () {
    if (typeof drawer.showModal === 'function') {
      drawer.showModal();
    } else {
      drawer.setAttribute('open', '');
    }
    root.classList.add('is-locked');
  });

  drawer.addEventListener('close', function () {
    root.classList.remove('is-locked');
  });

  Array.prototype.forEach.call(drawer.querySelectorAll('[data-close]'), function (button) {
    button.addEventListener('click', function () {
      drawer.close();
    });
  });

  drawerGo.addEventListener('click', function () {
    drawer.close();
    quoteSection.scrollIntoView();
    quoteSection.focus({ preventScroll: true });
  });

  /* Photo dropbox: resized on the device, then held in memory until sent. */

  function setPhotoStatus(text, tone) {
    photoStatus.textContent = text;
    photoStatus.setAttribute('data-tone', tone);
  }

  function isImageFile(file) {
    return file.type.indexOf('image/') === 0 || /\.(jpe?g|png|webp|gif|heic|heif)$/i.test(file.name || '');
  }

  function loadImage(file) {
    return new Promise(function (resolve, reject) {
      var url = URL.createObjectURL(file);
      var img = new Image();
      img.onload = function () {
        URL.revokeObjectURL(url);
        resolve(img);
      };
      img.onerror = function () {
        URL.revokeObjectURL(url);
        reject(new Error('Could not read the photo.'));
      };
      img.src = url;
    });
  }

  function resizePhoto(file) {
    return loadImage(file).then(function (img) {
      var width = img.naturalWidth;
      var height = img.naturalHeight;
      if (!width || !height) {
        throw new Error('Empty image.');
      }
      var scale = Math.min(1, maxSide / Math.max(width, height));
      var canvas = document.createElement('canvas');
      canvas.width = Math.max(1, Math.round(width * scale));
      canvas.height = Math.max(1, Math.round(height * scale));
      canvas.getContext('2d').drawImage(img, 0, 0, canvas.width, canvas.height);
      return new Promise(function (resolve, reject) {
        canvas.toBlob(function (blob) {
          if (blob) {
            resolve(blob);
          } else {
            reject(new Error('Could not encode the photo.'));
          }
        }, 'image/jpeg', 0.82);
      });
    }).then(function (blob) {
      return { blob: blob, url: URL.createObjectURL(blob) };
    }).catch(function () {
      return null;
    });
  }

  function renderPhotos() {
    photoList.textContent = '';
    photos.forEach(function (photo, index) {
      var item = document.createElement('li');
      var img = document.createElement('img');
      img.src = photo.url;
      img.alt = 'Car photo ' + (index + 1);
      var remove = document.createElement('button');
      remove.type = 'button';
      remove.className = 'photo-remove';
      remove.textContent = 'Remove';
      remove.setAttribute('aria-label', 'Remove car photo ' + (index + 1));
      remove.addEventListener('click', function () {
        URL.revokeObjectURL(photo.url);
        photos.splice(index, 1);
        renderPhotos();
        pickButton.focus();
      });
      item.appendChild(img);
      item.appendChild(remove);
      photoList.appendChild(item);
    });
    photoList.hidden = photos.length === 0;
    pickButton.disabled = photos.length >= photoLimit;
    pickButton.textContent = photos.length >= photoLimit
      ? 'All ' + photoLimit + ' photos added'
      : 'Choose photos (' + photos.length + ' of ' + photoLimit + ')';
  }

  function addFiles(fileList) {
    var files = Array.prototype.slice.call(fileList || []).filter(isImageFile);
    if (files.length === 0) {
      setPhotoStatus('Choose image files, such as JPEG, PNG or HEIC.', 'error');
      return;
    }
    var room = photoLimit - photos.length;
    if (room <= 0) {
      setPhotoStatus('You already have ' + photoLimit + ' photos. Remove one to add another.', 'error');
      return;
    }
    var chosen = files.slice(0, room);
    var extra = files.length - chosen.length;
    setPhotoStatus('Preparing ' + chosen.length + (chosen.length === 1 ? ' photo.' : ' photos.'), 'info');
    Promise.all(chosen.map(resizePhoto)).then(function (results) {
      var added = 0;
      results.forEach(function (photo) {
        if (photo) {
          photos.push(photo);
          added += 1;
        }
      });
      var failed = chosen.length - added;
      renderPhotos();
      var parts = [];
      if (added) {
        parts.push(added + (added === 1 ? ' photo added.' : ' photos added.'));
      }
      if (failed) {
        parts.push("Couldn't read " + failed + (failed === 1 ? ' photo' : ' photos') + '. Try a JPEG or PNG.');
      }
      if (extra) {
        parts.push('Only ' + photoLimit + ' photos fit. Remove one to add more.');
      }
      setPhotoStatus(parts.join(' '), failed || extra ? 'error' : 'ok');
    });
  }

  function clearPhotos() {
    photos.forEach(function (photo) {
      URL.revokeObjectURL(photo.url);
    });
    photos = [];
    renderPhotos();
    setPhotoStatus('', 'info');
  }

  pickButton.addEventListener('click', function () {
    fileInput.click();
  });

  fileInput.addEventListener('change', function () {
    addFiles(fileInput.files);
    fileInput.value = '';
  });

  ['dragenter', 'dragover'].forEach(function (type) {
    dropzone.addEventListener(type, function (event) {
      event.preventDefault();
      dropzone.classList.add('is-over');
    });
  });

  ['dragleave', 'drop'].forEach(function (type) {
    dropzone.addEventListener(type, function (event) {
      event.preventDefault();
      dropzone.classList.remove('is-over');
    });
  });

  dropzone.addEventListener('drop', function (event) {
    addFiles(event.dataTransfer && event.dataTransfer.files);
  });

  /* Sending */

  function buildRequest() {
    var values = new FormData(form);
    values.set('vehicle', selectedLabel(vehicleField));
    values.set('dirt', selectedLabel(dirtField));
    values.set('estimate', estimateSummary());
    values.set('photo_count', String(photos.length));
    photos.forEach(function (photo, index) {
      values.append('photos', photo.blob, 'car-photo-' + (index + 1) + '.jpg');
    });
    return values;
  }

  function requestText() {
    var values = new FormData(form);
    var lines = [
      'Quote request from the website',
      'Name: ' + values.get('name'),
      'Mobile: ' + values.get('mobile'),
      'Email: ' + values.get('email'),
      'Car: ' + values.get('car'),
      'Vehicle size: ' + selectedLabel(vehicleField),
      'How dirty: ' + selectedLabel(dirtField),
      'Suburb or postcode: ' + values.get('suburb'),
      'Services: ' + (picked.length ? picked.map(nameFor).join(', ') : 'none chosen'),
      'Estimate: ' + estimateSummary(),
      'Anything else: ' + values.get('message')
    ];
    if (photos.length) {
      lines.push('Photos: ' + photos.length + ' selected (not sent by this page, so attach them in your message)');
    }
    return lines.join('\n');
  }

  function sendToService() {
    submitButton.disabled = true;
    setStatus('Sending your request.', 'info');
    fetch(config.formEndpoint, {
      method: 'POST',
      headers: { Accept: 'application/json' },
      body: buildRequest()
    }).then(function (response) {
      if (!response.ok) {
        throw new Error('Send failed: ' + response.status);
      }
      form.reset();
      picked = [];
      clearPhotos();
      render();
      setStatus('Request sent. Thank you. ' + config.owner + ' will reply with your estimate.', 'ok');
    }).catch(function () {
      setStatus("Your request didn't send. Try again, or message " + config.owner + ' on Facebook.', 'error');
    }).then(function () {
      submitButton.disabled = false;
    });
  }

  function setStatus(text, tone) {
    statusLine.textContent = text;
    statusLine.setAttribute('data-tone', tone);
  }

  function fallbackRequest() {
    var text = requestText();
    var copied = navigator.clipboard && navigator.clipboard.writeText
      ? navigator.clipboard.writeText(text)
      : Promise.reject(new Error('Clipboard unavailable'));
    var photoNote = photos.length
      ? ' Photos are not sent from this page yet, so attach them in the message.'
      : '';
    copied.then(function () {
      setStatus("Online quote requests aren't set up yet. Your details are copied. Paste them into a Facebook message to " + config.owner + '.' + photoNote, 'info');
    }, function () {
      setStatus("Online quote requests aren't set up yet. Message " + config.owner + ' on Facebook with your car and what you need.' + photoNote, 'info');
    });
  }

  form.addEventListener('submit', function (event) {
    event.preventDefault();
    var nothingChosen = picked.length === 0 && messageField.value.trim() === '' && photos.length === 0;
    messageField.setCustomValidity(nothingChosen ? 'Choose a service, add a photo, or describe what you need.' : '');
    if (!form.reportValidity()) {
      return;
    }
    if (config.formEndpoint) {
      sendToService();
    } else {
      fallbackRequest();
    }
  });

  render();
  renderPhotos();
})();
