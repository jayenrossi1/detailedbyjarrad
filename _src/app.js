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
    var dirt = byId(dirts, dirtField.value);
    if (dirt && dirt.quote) {
      return { kind: 'quote' };
    }
    var size = vehicleField.value;
    var total = 0;
    var pending = false;
    picked.forEach(function (id) {
      var price = prices[id] ? prices[id][size] : null;
      if (typeof price === 'number') {
        total += price;
      } else {
        pending = true;
      }
    });
    return pending ? { kind: 'pending' } : { kind: 'price', total: total };
  }

  function estimateSummary() {
    var state = estimate();
    if (state.kind === 'price') {
      return money(state.total) + ' (estimate, final price confirmed by ' + config.owner + ')';
    }
    if (state.kind === 'quote') {
      return 'Heavy job, to be quoted from photos by ' + config.owner;
    }
    return state.kind === 'pending' ? 'To be confirmed by ' + config.owner : 'No services chosen';
  }

  function renderEstimate() {
    var state = estimate();
    estFigure.classList.toggle('is-pending', state.kind !== 'price');
    if (state.kind === 'empty') {
      estFigure.textContent = 'Choose a service';
      estNote.textContent = 'Pick at least one service from the menu. Your estimate updates as you choose.';
    } else if (state.kind === 'quote') {
      estFigure.textContent = 'Quoted from your photos';
      estNote.textContent = 'Heavy jobs are priced one by one. Add photos and ' + config.owner + ' will send your price.';
    } else if (state.kind === 'pending') {
      estFigure.textContent = 'To be confirmed';
      estNote.textContent = 'One or more of your services is priced on request. ' + config.owner + ' will confirm your price.';
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

  /* Email delivery through a form-to-email service: a plain form post, so the
     photos travel as ordinary file attachments. The page returns with ?sent=1. */
  function sendByPost() {
    var total = photos.reduce(function (sum, photo) {
      return sum + photo.blob.size;
    }, 0);
    if (total > 9 * 1024 * 1024) {
      setStatus('Your photos are too large to send together. Remove one and try again.', 'error');
      return;
    }
    submitButton.disabled = true;
    setStatus('Sending your request.', 'info');
    var values = new FormData(form);
    var post = document.createElement('form');
    post.method = 'post';
    post.action = config.formEndpoint;
    post.enctype = 'multipart/form-data';
    post.hidden = true;
    function add(name, value) {
      var input = document.createElement('input');
      input.type = 'hidden';
      input.name = name;
      input.value = value === null || value === undefined ? '' : String(value);
      post.appendChild(input);
    }
    add('_subject', 'Quote request from ' + values.get('name'));
    add('_template', 'table');
    add('_captcha', 'false');
    add('_next', location.origin + location.pathname + '?sent=1#quote');
    add('Name', values.get('name'));
    add('Mobile', values.get('mobile'));
    if (String(values.get('email') || '').trim()) {
      add('email', values.get('email'));
    }
    add('Car', values.get('car'));
    add('Vehicle size', selectedLabel(vehicleField));
    add('Condition', selectedLabel(dirtField));
    add('Suburb or postcode', values.get('suburb'));
    add('Services', picked.length ? picked.map(nameFor).join(', ') : 'None chosen');
    add('Estimate', estimateSummary());
    add('Anything else', values.get('message'));
    var attached = 0;
    try {
      photos.forEach(function (photo, index) {
        var transfer = new DataTransfer();
        transfer.items.add(new File([photo.blob], 'car-photo-' + (index + 1) + '.jpg', { type: 'image/jpeg' }));
        var input = document.createElement('input');
        input.type = 'file';
        input.name = 'photo_' + (index + 1);
        input.files = transfer.files;
        if (input.files.length === 1) {
          post.appendChild(input);
          attached += 1;
        }
      });
    } catch (error) {
      attached = 0;
    }
    add('Photos', photos.length
      ? attached + ' of ' + photos.length + ' attached' + (attached < photos.length ? '. Ask the customer to text the rest.' : '')
      : 'None');
    document.body.appendChild(post);
    post.submit();
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
    if (config.formEndpoint && config.formMode === 'post') {
      sendByPost();
    } else if (config.formEndpoint) {
      sendToService();
    } else {
      fallbackRequest();
    }
  });

  /* Merch cart. Orders go to the owner by text or email; he confirms and arranges payment. */
  (function () {
    var dialog = document.getElementById('cart');
    if (!dialog) {
      return;
    }
    var shop = config.merch || {};
    var fab = document.getElementById('cart-fab');
    var list = document.getElementById('cart-items');
    var emptyNote = document.getElementById('cart-empty');
    var checkout = document.getElementById('cart-checkout');
    var subCell = document.getElementById('cart-sub');
    var postCell = document.getElementById('cart-post');
    var totalCell = document.getElementById('cart-total');
    var smsLink = document.getElementById('cart-sms');
    var emailLink = document.getElementById('cart-email');
    var deliveryInputs = Array.prototype.slice.call(dialog.querySelectorAll('input[name="cart-delivery"]'));
    var cards = Array.prototype.slice.call(document.querySelectorAll('[data-product]'));
    var catalogue = {};
    var cart = [];
    var KEY = 'dbj-cart-v1';

    cards.forEach(function (card) {
      catalogue[card.getAttribute('data-product')] = {
        name: card.getAttribute('data-name'),
        price: parseInt(card.getAttribute('data-price'), 10)
      };
    });

    function dollars(cents) {
      return currency + (cents / 100).toFixed(2);
    }

    function save() {
      try {
        localStorage.setItem(KEY, JSON.stringify(cart.map(function (line) {
          return { id: line.id, size: line.size, qty: line.qty };
        })));
      } catch (error) { /* storage is a convenience only */ }
    }

    function load() {
      try {
        var saved = JSON.parse(localStorage.getItem(KEY) || '[]');
        saved.forEach(function (line) {
          var qty = parseInt(line.qty, 10);
          if (catalogue[line.id] && qty > 0 && qty < 100) {
            cart.push({ id: String(line.id), size: String(line.size || ''), qty: qty });
          }
        });
      } catch (error) {
        cart = [];
      }
    }

    function delivery() {
      var chosen = deliveryInputs.filter(function (input) {
        return input.checked;
      })[0];
      return chosen ? chosen.value : 'pickup';
    }

    function totals() {
      var sub = 0;
      var count = 0;
      cart.forEach(function (line) {
        sub += catalogue[line.id].price * line.qty;
        count += line.qty;
      });
      var posting = delivery() === 'post';
      var postage = posting && sub < (shop.freeOver || Infinity) ? (shop.postage || 0) : 0;
      if (!shop.freeOver && posting) {
        postage = shop.postage || 0;
      }
      return { sub: sub, count: count, posting: posting, postage: postage, total: sub + postage };
    }

    function label(line) {
      return catalogue[line.id].name + (line.size ? ' (' + line.size + ')' : '');
    }

    function orderText() {
      var sum = totals();
      var lines = ['Hi ' + config.owner + ", I'd like to order:"];
      cart.forEach(function (line) {
        lines.push(line.qty + ' x ' + label(line) + ' ' + dollars(catalogue[line.id].price * line.qty));
      });
      lines.push('Delivery: ' + (sum.posting
        ? 'Post (' + (sum.postage ? dollars(sum.postage) : 'free') + ')'
        : 'Pickup or drop-off' + (shop.area ? ' on the ' + shop.area : '')));
      lines.push('Total: ' + dollars(sum.total));
      lines.push('My name: ');
      if (sum.posting) {
        lines.push('Post to: ');
      }
      return lines.join('\n');
    }

    function qtyButton(text, name, onClick) {
      var button = document.createElement('button');
      button.type = 'button';
      button.className = 'cart-qty';
      button.textContent = text;
      button.setAttribute('aria-label', name);
      button.addEventListener('click', onClick);
      return button;
    }

    function renderCart() {
      var sum = totals();
      fab.hidden = sum.count === 0;
      fab.textContent = 'Cart (' + sum.count + ')';
      list.textContent = '';
      cart.forEach(function (line, index) {
        var row = document.createElement('li');
        var name = document.createElement('span');
        name.className = 'cart-line__name';
        name.textContent = label(line);
        var price = document.createElement('span');
        price.className = 'cart-line__price';
        price.textContent = dollars(catalogue[line.id].price * line.qty);
        var controls = document.createElement('div');
        controls.className = 'cart-line__controls';
        var qty = document.createElement('span');
        qty.textContent = line.qty;
        controls.appendChild(qtyButton('\u2212', 'One fewer ' + label(line), function () {
          line.qty -= 1;
          if (line.qty < 1) {
            cart.splice(index, 1);
          }
          update();
        }));
        controls.appendChild(qty);
        controls.appendChild(qtyButton('+', 'One more ' + label(line), function () {
          if (line.qty < 20) {
            line.qty += 1;
          }
          update();
        }));
        var remove = document.createElement('button');
        remove.type = 'button';
        remove.className = 'chip-remove';
        remove.textContent = 'Remove';
        remove.setAttribute('aria-label', 'Remove ' + label(line) + ' from cart');
        remove.addEventListener('click', function () {
          cart.splice(index, 1);
          update();
        });
        controls.appendChild(remove);
        row.appendChild(name);
        row.appendChild(price);
        row.appendChild(controls);
        list.appendChild(row);
      });
      emptyNote.hidden = cart.length > 0;
      checkout.hidden = cart.length === 0;
      subCell.textContent = dollars(sum.sub);
      postCell.textContent = sum.posting ? (sum.postage ? dollars(sum.postage) : 'Free postage') : 'Free';
      totalCell.textContent = dollars(sum.total);
      var text = encodeURIComponent(orderText());
      smsLink.hidden = !shop.phone;
      smsLink.href = 'sms:' + shop.phone + '?&body=' + text;
      emailLink.hidden = !config.email;
      emailLink.href = 'mailto:' + config.email + '?subject=' + encodeURIComponent('Merch order') + '&body=' + text;
    }

    function update() {
      save();
      renderCart();
    }

    cards.forEach(function (card) {
      var button = card.querySelector('button.product__add');
      if (!button) {
        return;
      }
      var select = card.querySelector('.product__size');
      var note = card.querySelector('.product__msg');
      button.addEventListener('click', function () {
        var id = card.getAttribute('data-product');
        var size = select ? select.value : '';
        if (select && !size) {
          note.textContent = 'Choose a size first.';
          note.removeAttribute('data-tone');
          select.focus();
          return;
        }
        var existing = cart.filter(function (line) {
          return line.id === id && line.size === size;
        })[0];
        if (existing) {
          existing.qty = Math.min(20, existing.qty + 1);
        } else {
          cart.push({ id: id, size: size, qty: 1 });
        }
        note.textContent = 'Added to cart.';
        note.setAttribute('data-tone', 'ok');
        update();
      });
    });

    deliveryInputs.forEach(function (input) {
      input.addEventListener('change', renderCart);
    });

    fab.addEventListener('click', function () {
      if (typeof dialog.showModal === 'function') {
        dialog.showModal();
      } else {
        dialog.setAttribute('open', '');
      }
      root.classList.add('is-locked');
    });

    dialog.addEventListener('close', function () {
      root.classList.remove('is-locked');
    });

    Array.prototype.forEach.call(dialog.querySelectorAll('[data-close]'), function (button) {
      button.addEventListener('click', function () {
        dialog.close();
      });
    });

    load();
    renderCart();
  })();

  render();
  renderPhotos();

  if (/[?&]sent=1/.test(location.search)) {
    setStatus('Request sent. Thank you. ' + config.owner + ' will reply with your estimate.', 'ok');
    if (window.history && history.replaceState) {
      history.replaceState(null, '', location.pathname + '#quote');
    }
  }
})();
