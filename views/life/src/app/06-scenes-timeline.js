  function roomScene(room, now) {
    if ((/阳台|露台/.test(room) ? use3DWorld() : use3D()) && window.Bedroom3D && Bedroom3D.supports && Bedroom3D.supports(room) && !state.placement) return Bedroom3D.markup(now, state.homeItems, sceneEnvironment(), (state.data || {}).appearance, room);
    if (window.SceneStudio) return SceneStudio.room(room, now, state.homeItems, sceneEnvironment(), (state.data || {}).appearance);
    var roomClass = ROOM_CLASS[room] || 'living';
    var key = activityKey(now && now.activity);
    var activity = escapeHtml((now && now.activity) || '自由时间');
    var label = escapeHtml(room || '家');
    var effects = effectsMarkup(key, 72, 58);
    var body = '';
    if (roomClass === 'bedroom') {
      body = [
        '<div class="room-back-wall"></div>',
        '<div class="room-floor"></div>',
        '<div class="room-window win-a"><i></i><i></i></div>',
        '<div class="room-art"></div>',
        '<div class="furn wardrobe"><i class="handle"></i></div>',
        '<div class="furn bed"><i class="pillow p1"></i><i class="pillow p2"></i><i class="blanket"></i></div>',
        '<div class="furn nightstand"><i class="lamp"></i></div>',
        '<div class="furn plant small"></div>',
        '<div class="room-rug"></div>',
        '<div class="room-label">' + label + '<small>在家 · ' + activity + '</small></div>',
        effects,
        standeeMarkup()
      ].join('');
    } else if (roomClass === 'bathroom') {
      body = [
        '<div class="room-back-wall tiled"></div>',
        '<div class="room-floor tiled"></div>',
        '<div class="room-window win-b"><i></i><i></i></div>',
        '<div class="furn mirror"></div>',
        '<div class="furn sink"><i></i></div>',
        '<div class="furn toilet"></div>',
        '<div class="furn towel"></div>',
        '<div class="furn tub"><i class="water"></i><i class="faucet"></i></div>',
        '<div class="bath-avatar"><img src="' + characterArtSrc() + '" onerror="this.onerror=null;this.src=\'assets/character_daily.png\'" alt=""></div>',
        '<div class="room-rug bath-mat"></div>',
        '<div class="room-label">' + label + '<small>在家 · ' + activity + '</small></div>',
        effects,
        '<div class="steam-cloud"><i></i><i></i><i></i></div>'
      ].join('');
    } else if (roomClass === 'study') {
      body = [
        '<div class="room-back-wall"></div>',
        '<div class="room-floor"></div>',
        '<div class="room-window win-c"><i></i><i></i></div>',
        '<div class="room-art corkboard"></div>',
        '<div class="furn bookshelf"><i></i><i></i><i></i><i></i></div>',
        '<div class="furn desk"><i class="monitor"></i><i class="keyboard"></i><i class="mug"></i></div>',
        '<div class="furn chair"></div>',
        '<div class="furn plant small"></div>',
        '<div class="room-rug"></div>',
        '<div class="room-label">' + label + '<small>在家 · ' + activity + '</small></div>',
        effects,
        standeeMarkup()
      ].join('');
    } else if (roomClass === 'kitchen') {
      body = [
        '<div class="room-back-wall tiled"></div>',
        '<div class="room-floor tiled"></div>',
        '<div class="room-window win-d"><i></i><i></i></div>',
        '<div class="furn upper-cabinets"></div>',
        '<div class="furn counter"><i class="sink"></i><i class="stove"></i><i class="pot"></i></div>',
        '<div class="furn fridge"><i class="handle"></i></div>',
        '<div class="furn dining-table"><i class="plate p1"></i><i class="plate p2"></i><i class="cup"></i></div>',
        '<div class="room-rug"></div>',
        '<div class="room-label">' + label + '<small>在家 · ' + activity + '</small></div>',
        effects,
        standeeMarkup()
      ].join('');
    } else if (roomClass === 'balcony') {
      body = [
        '<div class="room-back-wall balcony-sky"></div>',
        '<div class="room-floor balcony-deck"></div>',
        '<div class="room-window win-e"><i></i><i></i></div>',
        '<div class="furn railing"></div>',
        '<div class="furn balcony-plant p1"></div>',
        '<div class="furn balcony-plant p2"></div>',
        '<div class="furn balcony-plant p3"></div>',
        '<div class="furn balcony-chair"></div>',
        '<div class="furn balcony-table"><i></i></div>',
        '<div class="string-lights"><i></i><i></i><i></i><i></i><i></i></div>',
        '<div class="room-label">' + label + '<small>在家 · ' + activity + '</small></div>',
        effects,
        standeeMarkup()
      ].join('');
    } else if (roomClass === 'hall') {
      body = [
        '<div class="room-back-wall"></div>',
        '<div class="room-floor"></div>',
        '<div class="furn shoe-cabinet"><i></i></div>',
        '<div class="furn coat-rack"><i></i><i></i><i></i></div>',
        '<div class="furn hall-mirror"></div>',
        '<div class="room-rug hall-runner"></div>',
        '<div class="room-label">' + label + '<small>在家 · ' + activity + '</small></div>',
        effects,
        standeeMarkup()
      ].join('');
    } else {
      body = [
        '<div class="room-back-wall"></div>',
        '<div class="room-floor"></div>',
        '<div class="room-window win-a"><i></i><i></i></div>',
        '<div class="furn sofa"></div>',
        '<div class="furn coffee-table"><i></i></div>',
        '<div class="furn tv"><i></i></div>',
        '<div class="furn record"></div>',
        '<div class="furn plant"></div>',
        '<div class="room-rug"></div>',
        '<div class="room-art"></div>',
        '<div class="room-label">' + label + '<small>在家 · ' + activity + '</small></div>',
        effects,
        standeeMarkup()
      ].join('');
    }
    return '<div class="room-scene room-' + roomClass + '">' + body + activityProps(key) + '</div>';
  }

  function sceneBuildings() {
    return [
      '<div class="building b1"><i></i><i></i><i></i><i></i><i></i><i></i></div>',
      '<div class="building b2"><i></i><i></i><i></i><i></i></div>',
      '<div class="building b3"><i></i><i></i><i></i><i></i><i></i><i></i></div>',
      '<div class="building b4"><i></i><i></i><i></i><i></i></div>',
      '<div class="building b5"><i></i><i></i><i></i></div>',
      '<div class="antenna a1"></div><div class="antenna a2"></div>'
    ].join('');
  }

  function sceneTrees() {
    return [
      '<div class="tree t1"><span class="trunk"></span><span class="crown c1"></span><span class="crown c2"></span><span class="crown c3"></span></div>',
      '<div class="tree t2"><span class="trunk"></span><span class="crown c1"></span><span class="crown c2"></span><span class="crown c3"></span></div>',
      '<div class="tree t3"><span class="trunk"></span><span class="crown c1"></span><span class="crown c2"></span><span class="crown c3"></span></div>'
    ].join('');
  }

  function sceneAmbient() {
    return [
      '<div class="sky-birds"><i></i><i></i><i></i><i></i></div>',
      '<div class="ambient-motes"><i></i><i></i><i></i><i></i><i></i></div>',
      '<div class="foreground-bushes"><i class="fb1"></i><i class="fb2"></i><i class="fb3"></i></div>'
    ].join('');
  }

  function sceneProps(key, now) {
    if (key === 'nightmarket') {
      return [
        '<div class="nm-stall s1"><span class="awning"></span><i class="counter"></i><i class="lamp"></i></div>',
        '<div class="nm-stall s2"><span class="awning"></span><i class="counter"></i><i class="lamp"></i></div>',
        '<div class="nm-stall s3"><span class="awning"></span><i class="counter"></i><i class="lamp"></i></div>',
        '<div class="nm-string"><i></i><i></i><i></i><i></i><i></i><i></i><i></i></div>',
        '<div class="nm-lanterns"><i></i><i></i><i></i></div>',
        '<div class="nm-steam"><i></i><i></i><i></i></div>',
        '<div class="nm-sign">夜市</div>',
        '<div class="nm-stools"><i></i><i></i><i></i></div>',
        '<div class="nm-crates"><i></i><i></i></div>'
      ].join('');
    }
    if (key === 'station') {
      return [
        '<div class="station-roof"><i></i><i></i><i></i><i></i></div>',
        '<div class="station-train"><span class="nose"></span><i></i><i></i><i></i><i class="door"></i></div>',
        '<div class="station-rail"><i></i><i></i><i></i></div>',
        '<div class="station-platform"></div>',
        '<div class="station-line"></div>',
        '<div class="station-board"><span>12:40 · 京都</span><i></i></div>',
        '<div class="station-clock"><i></i></div>',
        '<div class="station-pillar p1"></div><div class="station-pillar p2"></div>',
        '<div class="station-bench"><i></i></div>',
        '<div class="station-luggage"><i></i><i></i></div>'
      ].join('');
    }
    if (key === 'airport') {
      return [
        '<div class="airport-terminal"><i></i><i></i><i></i><i></i><i></i><i></i></div>',
        '<div class="airport-tower"><span class="mast"></span><i class="light"></i></div>',
        '<div class="airport-runway"><i></i><i></i><i></i><i></i><i></i></div>',
        '<div class="airport-plane"><span class="body"></span><span class="wing"></span><span class="tail"></span><i></i><i></i><i></i></div>',
        '<div class="airport-board"><span>DEPARTURES</span><i></i><i></i><i></i></div>',
        '<div class="airport-luggage"><i></i><i></i></div>',
        '<div class="airport-cart"><span></span><i></i></div>',
        '<div class="airport-windsock"><span></span></div>',
        '<div class="airport-lights"><i></i><i></i><i></i><i></i><i></i><i></i></div>'
      ].join('');
    }
    if (key === 'hotel') {
      return [
        '<div class="hotel-building"><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i></div>',
        '<div class="hotel-sign">HOTEL</div>',
        '<div class="hotel-canopy"></div>',
        '<div class="hotel-door"><i></i><i></i></div>',
        '<div class="hotel-lamp l1"></div><div class="hotel-lamp l2"></div>',
        '<div class="hotel-planter p1"><i></i><i></i><i></i></div>',
        '<div class="hotel-cart"><span></span><i></i><i></i></div>',
        '<div class="hotel-flag"><span></span></div>',
        '<div class="hotel-steps"></div>'
      ].join('');
    }
    if (key === 'travel') {
      var cityName = (now && now.city) ? String(now.city) : 'CITY';
      return [
        '<div class="travel-row"><i></i><i></i><i></i><i></i><i></i></div>',
        '<div class="travel-roofs"><i></i><i></i><i></i></div>',
        '<div class="travel-bunting"><i></i><i></i><i></i><i></i><i></i><i></i></div>',
        '<div class="travel-lanterns"><i></i><i></i><i></i></div>',
        '<div class="travel-sign">' + escapeHtml(cityName) + '</div>',
        '<div class="travel-cobble"><i></i><i></i><i></i><i></i><i></i></div>',
        '<div class="travel-lamp l1"></div><div class="travel-lamp l2"></div>',
        '<div class="travel-cafe"><span class="table"></span><i></i><i></i></div>',
        '<div class="travel-fountain"><i></i></div>',
        '<div class="travel-pigeons"><i></i><i></i><i></i></div>'
      ].join('');
    }
    if (key === 'temple') {
      return [
        '<div class="temple-torii"><i class="beam"></i><i class="tie"></i><i class="post p1"></i><i class="post p2"></i></div>',
        '<div class="temple-hall"><span class="roof"></span><i class="pillar p1"></i><i class="pillar p2"></i><i class="door"></i></div>',
        '<div class="temple-lantern l1"><i></i></div><div class="temple-lantern l2"><i></i></div>',
        '<div class="temple-incense"><i></i><i></i><i></i></div>',
        '<div class="temple-emas"><i></i><i></i><i></i><i></i></div>',
        '<div class="temple-petals"><i></i><i></i><i></i><i></i><i></i></div>',
        '<div class="temple-path"></div>',
        '<div class="temple-bell"><span></span></div>'
      ].join('');
    }
    if (key === 'onsen') {
      return [
        '<div class="onsen-fence"><i></i><i></i><i></i><i></i><i></i><i></i></div>',
        '<div class="onsen-pool"><span class="ripple r1"></span><span class="ripple r2"></span></div>',
        '<div class="onsen-rocks"><i></i><i></i><i></i><i></i><i></i></div>',
        '<div class="onsen-steam"><i></i><i></i><i></i><i></i></div>',
        '<div class="onsen-lantern"><i></i></div>',
        '<div class="onsen-bucket"><span></span></div>',
        '<div class="onsen-towel"></div>',
        '<div class="onsen-pine"></div>'
      ].join('');
    }
    if (key === 'harbor') {
      return [
        '<div class="harbor-sea"><i class="harbor-wave w1"></i><i class="harbor-wave w2"></i></div>',
        '<div class="harbor-houses"><i></i><i></i><i></i><i></i></div>',
        '<div class="harbor-pier"></div>',
        '<div class="harbor-boat"><span class="hull"></span><span class="cabin"></span><span class="mast"></span><i></i></div>',
        '<div class="harbor-crates"><i></i><i></i></div>',
        '<div class="harbor-net"></div>',
        '<div class="harbor-gulls"><i></i><i></i><i></i></div>',
        '<div class="harbor-lighthouse"><i></i></div>'
      ].join('');
    }
    if (key === 'mountain') {
      return [
        '<div class="mountain-ridge r1"></div><div class="mountain-ridge r2"></div><div class="mountain-ridge r3"></div>',
        '<div class="mountain-mist m1"></div><div class="mountain-mist m2"></div>',
        '<div class="mountain-pines"><i></i><i></i><i></i></div>',
        '<div class="mountain-deck"><span class="rail"></span><i></i><i></i></div>',
        '<div class="mountain-scope"><span></span><i></i></div>',
        '<div class="mountain-cable"><span class="car"></span></div>',
        '<div class="mountain-birds"><i></i><i></i><i></i></div>'
      ].join('');
    }
    if (key === 'izakaya') {
      return [
        '<div class="izakaya-front"><span class="roof"></span><span class="noren"></span><i class="door"></i></div>',
        '<div class="izakaya-sign"><i></i><i></i><i></i></div>',
        '<div class="izakaya-lanterns"><i></i><i></i><i></i></div>',
        '<div class="izakaya-crates"><i></i><i></i><i></i></div>',
        '<div class="izakaya-stools"><i></i><i></i></div>',
        '<div class="izakaya-smoke"><i></i><i></i></div>',
        '<div class="izakaya-lamp"></div>'
      ].join('');
    }
    if (key === 'cafe') {
      return [
        '<div class="cafe-building"></div>',
        '<div class="cafe-awning"></div>',
        '<div class="cafe-sign">CAFE</div>',
        '<div class="cafe-window"><i></i><i></i></div>',
        '<div class="cafe-pastry"><i></i><i></i><i></i></div>',
        '<div class="cafe-table"><i class="cup"></i></div>',
        '<div class="cafe-chair"></div>',
        '<div class="street-lamp"><i></i></div>',
        '<div class="cafe-menu"><i></i><i></i><i></i></div>',
        '<div class="cafe-table t2"><i class="cup"></i></div>',
        '<div class="cafe-chair c2"></div>',
        '<div class="cafe-lights"><i></i><i></i><i></i><i></i><i></i></div>',
        '<div class="cafe-planter"><i></i><i></i><i></i></div>'
      ].join('');
    }
    if (key === 'park') {
      return [
        '<div class="park-pond"></div>',
        '<div class="park-bench"><i></i><i></i></div>',
        '<div class="park-duck d1"></div>',
        '<div class="park-duck d2"></div>',
        '<div class="park-leaves"><i></i><i></i><i></i><i></i></div>',
        '<div class="park-flowers"><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i></div>',
        '<div class="park-lamp l1"></div><div class="park-lamp l2"></div>',
        '<div class="park-lily l1"></div><div class="park-lily l2"></div><div class="park-lily l3"></div>',
        '<div class="park-reeds"><i></i><i></i><i></i><i></i></div>',
        '<div class="park-fountain"></div>',
        '<div class="park-bench b2"><i></i><i></i></div>',
        '<div class="park-butterflies"><i></i><i></i></div>',
        '<div class="park-kite"><i></i></div>'
      ].join('');
    }
    if (key === 'bookstore') {
      return [
        '<div class="shop bookstore"><div class="shop-window"><i></i><i></i><i></i><i></i></div><div class="shop-awning"></div></div>',
        '<div class="floating-pages"><i></i><i></i><i></i></div>',
        '<div class="bookcart"><i></i><i></i><i></i></div>',
        '<div class="book-open-sign">OPEN</div>',
        '<div class="book-plant"><i></i><i></i><i></i></div>',
        '<div class="book-bench"><i></i><i></i></div>',
        '<div class="book-ladder"></div>',
        '<div class="book-stack"><i></i><i></i><i></i><i></i></div>'
      ].join('');
    }
    if (key === 'museum') {
      return [
        '<div class="museum-building"></div>',
        '<div class="museum-column c1"></div><div class="museum-column c2"></div><div class="museum-column c3"></div>',
        '<div class="museum-frame f1"></div><div class="museum-frame f2"></div>',
        '<div class="museum-spot"></div>',
        '<div class="museum-statue"><i></i></div>',
        '<div class="museum-pedestal"></div>',
        '<div class="museum-banner">ART</div>',
        '<div class="museum-rope r1"></div><div class="museum-rope r2"></div>',
        '<div class="museum-bench"><i></i><i></i></div>',
        '<div class="museum-steps"></div>',
        '<div class="museum-flags"><i></i><i></i><i></i><i></i></div>'
      ].join('');
    }
    if (key === 'cinema') {
      return [
        '<div class="cinema-building"></div>',
        '<div class="cinema-marquee">NOW SHOWING</div>',
        '<div class="cinema-screen"></div>',
        '<div class="cinema-seats"><i></i><i></i><i></i></div>',
        '<div class="popcorn"></div>',
        '<div class="cinema-poster p1"></div><div class="cinema-poster p2"></div>',
        '<div class="cinema-ticket"><i></i></div>',
        '<div class="cinema-carpet"></div>',
        '<div class="cinema-rope r1"></div><div class="cinema-rope r2"></div>',
        '<div class="cinema-bulbs"><i></i><i></i><i></i><i></i><i></i><i></i></div>',
        '<div class="cinema-stars"><i></i><i></i><i></i></div>',
        '<div class="cinema-reel"></div>'
      ].join('');
    }
    if (key === 'beach') {
      return [
        '<div class="sea"></div>',
        '<div class="wave w1"></div><div class="wave w2"></div>',
        '<div class="palm"><i></i><span></span></div>',
        '<div class="birds"><i></i><i></i><i></i></div>',
        '<div class="beach-umbrella"></div>',
        '<div class="beach-towel"></div>',
        '<div class="beach-star s1"></div><div class="beach-star s2"></div>',
        '<div class="beach-shell sh1"></div><div class="beach-shell sh2"></div>',
        '<div class="beach-driftwood"></div>',
        '<div class="beach-lighthouse"><i></i></div>',
        '<div class="beach-umbrella u2"></div>',
        '<div class="beach-sailboat"><i></i></div>',
        '<div class="beach-lifebuoy"></div>'
      ].join('');
    }
    if (key === 'mall') {
      return [
        '<div class="mall-building"><i></i><i></i><i></i><i></i></div>',
        '<div class="neon-sign n1">SALE</div>',
        '<div class="neon-sign n2">MALL</div>',
        '<div class="shopping-bags"><i></i><i></i></div>',
        '<div class="mall-mannequin m1"><i></i></div><div class="mall-mannequin m2"><i></i></div>',
        '<div class="mall-planter p1"><i></i><i></i></div>',
        '<div class="mall-planter p2"><i></i><i></i></div>',
        '<div class="mall-banner">NEW</div>',
        '<div class="mall-bench"><i></i><i></i></div>',
        '<div class="sky-balloons"><i></i><i></i><i></i></div>'
      ].join('');
    }
    if (key === 'office') {
      return [
        '<div class="office-building"><i></i><i></i><i></i><i></i><i></i><i></i></div>',
        '<div class="office-desk"></div>',
        '<div class="office-monitor"></div>',
        '<div class="office-cup"></div>',
        '<div class="office-plant"></div>',
        '<div class="office-desk d2"></div>',
        '<div class="office-monitor m2"></div>',
        '<div class="office-chair"></div>',
        '<div class="office-whiteboard"><i></i></div>',
        '<div class="office-cooler"></div>',
        '<div class="office-cabinet"></div>',
        '<div class="office-clock"><i></i></div>'
      ].join('');
    }
    if (key === 'street') {
      return [
        '<div class="street-shop s1"><i></i><i></i></div>',
        '<div class="street-shop s2"><i></i><i></i></div>',
        '<div class="lantern l1"></div><div class="lantern l2"></div><div class="lantern l3"></div>',
        '<div class="bike"><i></i><i></i></div>',
        '<div class="street-shop s3"><i></i><i></i></div>',
        '<div class="street-awning"></div>',
        '<div class="street-sign">茶</div>',
        '<div class="street-planter p1"><i></i><i></i></div>',
        '<div class="street-planter p2"><i></i><i></i></div>',
        '<div class="street-bench"><i></i><i></i></div>',
        '<div class="lantern l4"></div><div class="lantern l5"></div>',
        '<div class="street-banners"><i></i><i></i><i></i><i></i></div>'
      ].join('');
    }
    if (key === 'food') {
      return [
        '<div class="food-stall"></div>',
        '<div class="food-awning"></div>',
        '<div class="food-steam"><i></i><i></i><i></i></div>',
        '<div class="food-bowl"></div>',
        '<div class="food-stool"></div>',
        '<div class="food-crate c1"><i></i><i></i><i></i></div>',
        '<div class="food-crate c2"><i></i><i></i></div>',
        '<div class="food-menu">MENU</div>',
        '<div class="food-lantern l1"></div><div class="food-lantern l2"></div>',
        '<div class="food-stool s2"></div>',
        '<div class="food-bench"><i></i><i></i></div>',
        '<div class="food-skewers"><i></i><i></i><i></i></div>'
      ].join('');
    }
    if (key === 'supermarket') {
      return [
        '<div class="supermarket-building"><i></i><i></i><i></i><i></i></div>',
        '<div class="supermarket-sign">FRESH</div>',
        '<div class="supermarket-door"><i></i><i></i></div>',
        '<div class="supermarket-shelf"><i></i><i></i><i></i><i></i><i></i><i></i></div>',
        '<div class="supermarket-cart"><i></i><i></i></div>',
        '<div class="supermarket-produce"><i></i><i></i><i></i></div>',
        '<div class="supermarket-checkout"></div>',
        '<div class="supermarket-bags"><i></i><i></i></div>'
      ].join('');
    }
    if (key === 'grocery') {
      return [
        '<div class="grocery-building"></div>',
        '<div class="grocery-awning"></div>',
        '<div class="grocery-sign">杂货</div>',
        '<div class="grocery-window"><i></i><i></i></div>',
        '<div class="grocery-jars"><i></i><i></i><i></i></div>',
        '<div class="grocery-sacks"><i></i><i></i></div>',
        '<div class="grocery-counter"></div>',
        '<div class="grocery-lantern"></div>'
      ].join('');
    }
    if (key === 'market') {
      return [
        '<div class="market-awning"></div>',
        '<div class="market-stall s1"><i></i><i></i></div>',
        '<div class="market-stall s2"><i></i><i></i></div>',
        '<div class="market-produce"><i></i><i></i><i></i><i></i></div>',
        '<div class="market-fish"><i></i></div>',
        '<div class="market-basket"><i></i></div>',
        '<div class="market-lantern l1"></div><div class="market-lantern l2"></div>'
      ].join('');
    }
    if (key === 'transit') {
      return [
        '<div class="road"></div>',
        '<div class="sidewalk"></div>',
        '<div class="road-line"></div>',
        '<div class="transit-crosswalk"></div>',
        '<div class="bus"><i></i><i></i><i></i></div>',
        '<div class="car c1"><i></i></div>',
        '<div class="car c2"><i></i></div>',
        '<div class="bus-stop"></div>',
        '<div class="transit-shelter"><i></i></div>',
        '<div class="transit-light"><i></i><i></i><i></i></div>',
        '<div class="transit-sign">BUS</div>',
        '<div class="transit-lamp l1"></div><div class="transit-lamp l2"></div>'
      ].join('');
    }
    return [
      '<div class="generic-shop"><i></i><i></i></div>',
      '<div class="generic-tree"></div>',
      '<div class="generic-bench"><i></i><i></i></div>',
      '<div class="generic-lamp"></div>',
      '<div class="generic-planter"><i></i><i></i><i></i></div>',
      '<div class="generic-sign">CITY</div>',
      '<div class="generic-bush b1"></div><div class="generic-bush b2"></div>',
      '<div class="sky-balloons"><i></i><i></i></div>'
    ].join('');
  }

  function outdoorScene(key, now, preview) {
    var label = sceneLabel(key);
    var city = (now && now.city) || '';
    if (key === 'travel' && city) label = city + ' · 街景';
    var travelKeys = { airport: 1, station: 1, hotel: 1, travel: 1 };
    var activity = (now && now.activity) || '';
    var effectKey = key === 'cafe' || key === 'food' || key === 'nightmarket' ? 'food' : activityKey(activity);
    var walking = key === 'transit' || hasAny(activity, [
      '走路', '步行', '散步', '回家', '前往', '赶路', '走去', '通勤', '出发', '出门'
    ]);
    var journeyMode = key === 'transit' ? SceneStudio.travelMode(preview ? null : now) : '';
    if (journeyMode) walking = journeyMode === 'walk' || journeyMode === 'cycle';
    var characterClass = 'scene-character' + (walking ? ' walking' : '');
    var wrapClass = 'scene-character-wrap' + (walking ? ' walking' : '');
    var statusText = preview ? '预览' : journeyMode ? ({walk:'步行中',cycle:'骑行中',bus:'乘公交中',car:'乘车中',rail:'乘列车中'}[journeyMode]) : walking ? '走路中' : travelKeys[key] ? '旅行中' : '外出中';
    var extra = key === 'beach' ? 'beach-sun' : '';
    var environment = sceneEnvironment();
    var band = environment.band;
    var html2d = [
      '<div class="scene studio-outdoor scene-' + key + ' scene-' + band + SceneStudio.classes(environment) + (journeyMode ? ' journey journey-' + journeyMode : '') + '" style="--sky-top:' + environment.sky[0] + ';--sky-bottom:' + environment.sky[1] + '">',
      '<div class="scene-sky"></div>',
      '<div class="scene-sun ' + extra + '"></div>',
      '<div class="scene-cloud c1"></div><div class="scene-cloud c2"></div><div class="scene-cloud c3"></div>' +
        '<div class="scene-cloud c4"></div><div class="scene-cloud c5"></div>',
      '<div class="scene-ground"></div>',
      '<div class="scene-buildings">' + sceneBuildings() + '</div>',
      '<div class="scene-trees">' + sceneTrees() + '</div>',
      '<div class="scene-path"></div>',
      '<div class="scene-props">' + sceneProps(key, now) + '</div>',
      (journeyMode ? SceneStudio.journeyDecor(environment, journeyMode) : SceneStudio.outdoorDecor(key, environment)),
      '<div class="scene-timewash"></div>',
      SceneStudio.precipitation(environment, false),
      SceneStudio.badge(environment),
      (/rain|storm/.test(environment.weather) ? '<div class="scene-weather-reflection"></div>' : ''),
      '<div class="scene-stars"><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i></div>',
      '<div class="scene-ambient">' + sceneAmbient() + '</div>',
      '<div class="' + wrapClass + '">',
      (walking ? '<div class="walk-dust"><i></i><i></i><i></i></div>' : ''),
      '<div class="' + characterClass + '"><img src="' + characterArtSrc() + '" onerror="this.onerror=null;this.src=\'assets/character_daily.png\'" alt="白紫固定立绘"></div>',
      '<div class="scene-effects">' + effectsMarkup(effectKey, 66, 58) + '</div>',
      '</div>',
      '<div class="scene-label"><span class="scene-label-icon">' + sceneIconSvg(key) +
        '</span>' + escapeHtml(label) + '<small>' + statusText + '</small>' +
        (sceneInteriorName(key) ? '<button type="button" class="scene-mode-toggle" data-scene-mode="indoor">室内</button>' : '') +
        '</div>',
      '</div>'
    ].join('');
    return destination3d(key, 'outdoor', label, statusText, environment, html2d, sceneInteriorName(key) ? 'indoor' : '', journeyMode);
  }

  // 3D outing scenes (assets/destination-3d.js); the 2D art above stays as the fallback.
  function destination3d(key, view, label, status, environment, html2d, toggleTo, mode) {
    if (!use3DWorld() || !window.Room3D || !Room3D.destinationMarkup || !Room3D.supportsDestination(key, view)) return html2d;
    var toggle = toggleTo ? '<button type="button" class="scene-mode-toggle" data-scene-mode="' + toggleTo + '">' + (toggleTo === 'indoor' ? '室内' : '室外') + '</button>' : '';
    var labelHtml = '<div class="scene-label"><span class="scene-label-icon">' + sceneIconSvg(key) + '</span>' + escapeHtml(label) + '<small>' + escapeHtml(status) + '</small>' + toggle + '</div>';
    var appearance = (state.data && state.data.appearance) || {};
    var look = {
      src: characterArtSrc(),
      key: appearance.key || 'daily',
      name: appearance.name || ''
    };
    return Room3D.destinationMarkup({ key: key, view: view, mode: mode || '', env: environment, labelHtml: labelHtml, fallback: html2d, look: look });
  }

  function indoorScene(key, now, preview) {
    var label = sceneLabel(key);
    var city = (now && now.city) || '';
    if (key === 'travel' && city) label = city + ' · 室内';
    var interior = sceneInteriorName(key);
    if (!interior || !window.GarageDestinations) {
      return outdoorScene(key, now, preview);
    }
    var environment = sceneEnvironment();
    var activity = (now && now.activity) || '';
    var effectKey = key === 'cafe' || key === 'food' || key === 'nightmarket' ? 'food' : activityKey(activity);
    var html2d = [
      '<div class="scene studio-indoor scene-' + key + ' ' + SceneStudio.classes(environment) + '">',
      '<div class="scene-indoor-art">' + GarageDestinations.interior(interior, environment) + '</div>',
      '<div class="scene-indoor-wash"></div>',
      SceneStudio.badge(environment),
      '<div class="scene-character-wrap">',
      '<div class="scene-character"><img src="' + characterArtSrc() + '" onerror="this.onerror=null;this.src=\'assets/character_daily.png\'" alt="白紫固定立绘"></div>',
      '<div class="scene-effects">' + effectsMarkup(effectKey, 66, 58) + '</div>',
      '</div>',
      '<div class="scene-label"><span class="scene-label-icon">' + sceneIconSvg(key) +
        '</span>' + escapeHtml(label) + '<small>' +
        (preview ? '预览 · 室内' : '室内') + '</small>' +
        '<button type="button" class="scene-mode-toggle" data-scene-mode="outdoor">室外</button>' +
        '</div>',
      '</div>'
    ].join('');
    return destination3d(key, 'indoor', label, preview ? '预览 · 室内' : '室内', environment, html2d, 'outdoor');
  }

  function flashSceneMode(text) {
    var stage = $('scene-stage');
    if (!stage) return;
    var previous = stage.querySelector('.scene-mode-flash');
    if (previous) previous.remove();
    var node = document.createElement('div');
    node.className = 'scene-mode-flash';
    node.textContent = text;
    stage.appendChild(node);
    window.setTimeout(function () {
      if (node.parentNode) node.remove();
    }, 900);
  }

  function renderScene(force) {
    var data = state.data || {};
    var signature = sceneSignature(data);
    if (!force && signature === renderState.scene) return;
    renderState.scene = signature;
    var now = data.now || null;
    var stage = $('scene-stage');
    var picker = $('scene-picker');
    var previewBadge = $('preview-badge');
    if (!now) {
      stage.innerHTML = '<div class="empty-scene"><span>今天还没有当前活动</span><small>先在模拟人生_世界插件里生成日程</small></div>';
      picker.classList.add('hidden');
      previewBadge.classList.add('hidden');
      $('activity').textContent = '自由时间';
      $('location').textContent = data.plans_path || '未连接';
      $('state-pill').className = 'pill';
      $('state-pill').textContent = '状态 · --';
      $('avail-pill2').className = 'pill';
      $('avail-pill2').textContent = '可打扰 · --';
      $('next-line').textContent = '';
      return;
    }
    var kind = now.kind;
    var actualScene = sceneFor(now);
    var previewScene = state.previewScene && (kind === 'home' || state.previewScene !== actualScene) ? state.previewScene : null;
    var sceneKey = previewScene || actualScene;
    var placement = kind === 'home' ? state.placement : null;
    var previewRoom = kind === 'home' ? state.previewRoom : null;
    var previewReturn = $('preview-return');
    if (placement) {
      stage.innerHTML = roomScene(placement.room, now);
      stage.classList.add('placement-mode');
      picker.classList.add('hidden');
      previewBadge.classList.remove('hidden');
      previewBadge.textContent = '摆放 · 点击地面选择位置';
      if (previewReturn) {
        previewReturn.classList.remove('hidden');
        previewReturn.textContent = '取消摆放';
      }
    } else if (previewRoom) {
      stage.innerHTML = roomScene(previewRoom, now);
      stage.classList.remove('placement-mode');
      picker.classList.add('hidden');
      previewBadge.classList.remove('hidden');
      previewBadge.textContent = '查看 · ' + previewRoom;
      if (previewReturn) {
        previewReturn.classList.remove('hidden');
        previewReturn.textContent = '回到当前';
      }
    } else {
      stage.classList.remove('placement-mode');
      if (previewReturn) previewReturn.textContent = '回到当前';
      if (kind === 'home' && !previewScene) {
        stage.innerHTML = roomScene(roomFor(now) || '客厅', now);
        picker.classList.remove('hidden');
        previewBadge.classList.add('hidden');
      } else {
        stage.innerHTML = state.indoorView && sceneInteriorName(sceneKey)
          ? indoorScene(sceneKey, now, Boolean(previewScene))
          : outdoorScene(sceneKey, now, Boolean(previewScene));
        picker.classList.remove('hidden');
        if (previewScene) {
          previewBadge.classList.remove('hidden');
          previewBadge.textContent = '预览 · ' + sceneLabel(sceneKey) +
            (state.indoorView && sceneInteriorName(sceneKey) ? ' · 室内' : '');
          if (previewReturn) previewReturn.classList.remove('hidden');
        } else {
          previewBadge.classList.add('hidden');
          if (previewReturn) previewReturn.classList.add('hidden');
        }
      }
    }
    $('activity').textContent = now.activity || '暂无活动';
    $('location').textContent = now.location || '未知';
    var statePill = $('state-pill');
    statePill.className = 'pill';
    statePill.textContent = '状态 · ' + (STATE_LABEL[now.state] || now.state || '--');
    var availPill = $('avail-pill2');
    availPill.className = 'pill ' + pillClassForAvailability(now.availability);
    availPill.textContent = '可打扰 · ' + (AVAIL_LABEL[now.availability] || now.availability || '--');
    var dot = $('now-dot');
    dot.style.background = kind === 'outside' ? 'var(--blue)' : kind === 'transit' ? 'var(--amber)' : 'var(--green)';
    dot.style.boxShadow = '0 0 12px ' + (kind === 'outside' ? 'rgba(125,200,255,.7)' : kind === 'transit' ? 'rgba(240,184,110,.7)' : 'rgba(125,219,166,.7)');
    var next = data.next && data.next[0];
    $('next-line').innerHTML = next
      ? '<b>下一站</b> ' + escapeHtml(next.start + '–' + next.end) + ' · ' +
        escapeHtml(next.activity) + ' <span style="color:var(--blue)">' + escapeHtml(next.location) + '</span>'
      : '<b>下一站</b> 今天没有后续安排了';
  }

  function nextWaitText(startText) {
    var now = timeToMinutes(clockText());
    var start = timeToMinutes(startText);
    if (!start) return '';
    var diff = start - now;
    if (diff <= 0) return '现在';
    if (diff < 60) return diff + ' 分钟后';
    var hours = Math.floor(diff / 60);
    var minutes = diff % 60;
    return hours + ' 小时' + (minutes ? ' ' + minutes + ' 分' : '') + '后';
  }

  function renderNext() {
    var data = state.data || {};
    var signature = JSON.stringify([
      data.persona, data.next || [], data.outfit || {},
      data.appearance || {}, clockText().slice(0, 5)
    ]);
    if (signature === renderState.next) return;
    renderState.next = signature;
    var list = $('next-list');
    var next = data.next || [];
    if (!next.length) {
      list.innerHTML = '<div class="empty-next">今天没有后续安排了</div>';
    } else {
      list.innerHTML = next.map(function (item, index) {
        return '<div class="next-item' + (index === 0 ? ' primary' : '') +
          '" data-next-index="' + index + '" title="' + escapeHtml((item.start || '') + '–' + (item.end || '') +
            ' · ' + (item.activity || '') + ' · ' + (item.location || '')) + '">' +
          '<span class="dot ' + categoryClass(item) + '"></span>' +
          '<div><div class="time">' + escapeHtml(item.start + '–' + item.end) +
          '<span class="next-countdown">' + escapeHtml(nextWaitText(item.start)) +
          '</span></div>' +
          '<div class="activity">' + escapeHtml(item.activity) + '</div></div>' +
          '<div class="place">' + escapeHtml(item.location) + '</div>' +
          '</div>';
      }).join('');
    }
    var outfit = data.outfit || {};
    var text = outfit.style && outfit.summary
      ? outfit.style + ' · ' + outfit.summary
      : (outfit.summary || outfit.style || '还没有穿搭记录');
    var appearance = data.appearance || {};
    if (appearance.is_sleepwear) {
      $('outfit-text').textContent = appearance.name || '睡衣';
    } else if (appearance.key === 'daily_outfit' || String(appearance.key || '').indexOf('daily_outfit') === 0) {
      $('outfit-text').textContent = text || '按今日穿搭';
    } else {
      $('outfit-text').textContent = appearance.name
        ? appearance.name + ' · 日常与外出服装'
        : text;
    }
  }

  function timeToMinutes(text) {
    var parts = String(text || '').split(':');
    if (parts.length < 2) return 0;
    return Number(parts[0]) * 60 + Number(parts[1]);
  }

  function activityStateLabel(state) {
    var text = String(state || '').trim().toLowerCase();
    var labels = {
      sleep: '睡眠', sleeping: '睡眠', rest: '休息', resting: '休息',
      busy: '忙碌', available: '空闲', free: '空闲',
      work: '工作', working: '工作', at_work: '工作',
      commute: '路上', transit: '路上', travelling: '路上',
      dining: '用餐', eating: '用餐', meal: '用餐',
      shopping: '购物', reading: '阅读', cooking: '做饭',
      bath: '洗漱', bathing: '泡澡', exercise: '运动',
      study: '学习', studying: '学习', leisure: '休闲'
    };
    return labels[text] || String(state || '') || '--';
  }

  function scheduleSceneAvailable(item) {
    return Boolean(
      item && item.scene &&
      item.kind !== 'home' && item.kind !== 'sleep'
    );
  }

  function openScheduleDetail(item) {
    if (!item) return;
    state.scheduleItem = item;
    var body = $('schedule-body');
    if (!body) return;
    $('schedule-title').textContent = '日程详情';
    $('schedule-sub').textContent = '这一段时间她在做什么';
    var kinds = {
      home: '在家', outside: '外出', transit: '路上', sleep: '睡眠'
    };
    var rows = [
      ['时间', (item.start || '') + '–' + (item.end || '')],
      ['活动', item.activity || '--'],
      ['地点', item.location || '--'],
      ['类型', kinds[item.kind] || item.state || item.kind || '--'],
      ['状态', activityStateLabel(item.state)]
    ];
    var durationMinutes = Math.max(
      0,
      Number(item.end_min || 0) - Number(item.start_min || 0)
    );
    if (durationMinutes > 0) {
      var hours = Math.floor(durationMinutes / 60);
      var minutes = durationMinutes % 60;
      rows.splice(1, 0, ['时长', hours > 0
        ? hours + ' 小时' + (minutes ? ' ' + minutes + ' 分钟' : '')
        : minutes + ' 分钟']);
    }
    if (item.room) rows.push(['房间', item.room]);
    var canPreviewScene = scheduleSceneAvailable(item);
    if (canPreviewScene) rows.push(['场景', sceneLabel(item.scene)]);
    body.innerHTML = '<div class="schedule-detail-title">' +
      escapeHtml(item.activity || '一段日程') + '</div>' +
      '<div class="schedule-detail-rows">' + rows.map(function (row) {
        return '<div><small>' + escapeHtml(row[0]) + '</small><b>' +
          escapeHtml(String(row[1])) + '</b></div>';
      }).join('') + '</div>' +
      (canPreviewScene
        ? '<button type="button" class="cook-main-btn schedule-preview" ' +
          'id="schedule-preview">看看这个场景</button>'
        : '');
    $('schedule-modal').classList.remove('hidden');
  }

  function previewScheduleScene() {
    var item = state.scheduleItem;
    if (!scheduleSceneAvailable(item)) return;
    state.previewScene = item.scene;
    closeScheduleDetail();
    renderScene(true);
    showToast('场景预览：' + sceneLabel(item.scene));
  }

  function openDaySchedule() {
    var data = state.data || {};
    var timeline = data.timeline || [];
    var body = $('schedule-body');
    if (!body) return;
    var kinds = { home: '在家', outside: '外出', transit: '路上', sleep: '睡眠' };
    var counts = { home: 0, outside: 0, transit: 0 };
    timeline.forEach(function (item) {
      if (counts[item.kind] != null) counts[item.kind] += 1;
    });
    var dayFilter = state.dayScheduleFilter || 'all';
    var entries = timeline.map(function (item, index) {
      return { item: item, index: index };
    }).filter(function (entry) {
      return dayFilter === 'all' || entry.item.kind === dayFilter;
    });
    $('schedule-title').textContent = '今日日程';
    $('schedule-sub').textContent = (data.plan_date || '今天') +
      ' · 共 ' + timeline.length + ' 段 · 在家 ' + counts.home +
      ' / 外出 ' + counts.outside + ' / 路上 ' + counts.transit;
    if (!timeline.length) {
      body.innerHTML = '<p class="inventory-empty">今天还没有日程。</p>';
      $('schedule-modal').classList.remove('hidden');
      return;
    }
    var filters = [
      ['all', '全部'], ['home', '在家'],
      ['outside', '外出'], ['transit', '路上']
    ];
    body.innerHTML = '<div class="schedule-day-tools">' +
      '<div class="schedule-day-filters">' +
      filters.map(function (filter) {
        var filterCount = filter[0] === 'all'
          ? timeline.length
          : (counts[filter[0]] || 0);
        return '<button type="button" data-day-filter="' + filter[0] + '"' +
          (dayFilter === filter[0] ? ' class="active"' : '') + '>' +
          filter[1] + ' <b>' + filterCount + '</b></button>';
      }).join('') + '</div>' +
      '<button type="button" class="mini-btn" data-day-export="1">导出今日日程</button>' +
      '</div><div class="schedule-day-list">' +
      (entries.length
        ? entries.map(function (entry) {
            var item = entry.item;
            var isNow = data.now && String(data.now.id) === String(item.id);
            return '<button type="button" class="schedule-day-row' +
              (isNow ? ' current' : '') + '" data-day-index="' + entry.index + '">' +
              '<span class="schedule-day-time">' + escapeHtml(item.start || '') +
              '–' + escapeHtml(item.end || '') + '</span>' +
              '<span class="schedule-day-main"><b>' +
              escapeHtml(item.activity || '一段日程') + '</b><small>' +
              escapeHtml(item.location || '') + ' · ' +
              escapeHtml(kinds[item.kind] || item.kind || '') +
              (activityStateLabel(item.state) &&
               activityStateLabel(item.state) !== '--'
                ? ' · ' + escapeHtml(activityStateLabel(item.state))
                : '') +
              '</small></span>' +
              (isNow ? '<em>现在</em>' : '') +
              '</button>';
          }).join('')
        : '<p class="inventory-empty">这个分类今天没有日程。</p>') +
      '</div>';
    $('schedule-modal').classList.remove('hidden');
    var currentRow = body.querySelector('.schedule-day-row.current');
    if (currentRow && currentRow.scrollIntoView) {
      currentRow.scrollIntoView({ block: 'center', behavior: 'auto' });
    }
  }

  function exportDaySchedule() {
    var data = state.data || {};
    var filter = state.dayScheduleFilter || 'all';
    var filterLabels = {
      all: '全部', home: '在家', outside: '外出', transit: '路上'
    };
    var timeline = (data.timeline || []).filter(function (item) {
      return filter === 'all' || item.kind === filter;
    });
    if (!timeline.length) {
      showToast(filter === 'all'
        ? '今天还没有日程'
        : '当前分类今天没有日程');
      return;
    }
    var lines = [[
      '时间', '时长', '活动', '地点', '类型', '状态'
    ].map(csvCell).join(',')];
    timeline.forEach(function (item) {
      var minutes = Math.max(
        0,
        Number(item.end_min || 0) - Number(item.start_min || 0)
      );
      var duration = minutes > 0
        ? (minutes >= 60
          ? Math.floor(minutes / 60) + ' 小时' +
            (minutes % 60 ? ' ' + (minutes % 60) + ' 分钟' : '')
          : minutes + ' 分钟')
        : '';
      lines.push([
        (item.start || '') + '–' + (item.end || ''),
        duration,
        item.activity || '',
        item.location || '',
        item.kind || '',
        activityStateLabel(item.state)
      ].map(csvCell).join(','));
    });
    var blob = new Blob(['\ufeff' + lines.join('\r\n')], {
      type: 'text/csv;charset=utf-8'
    });
    var url = URL.createObjectURL(blob);
    var link = document.createElement('a');
    link.href = url;
    link.download = '今日日程-' + String(data.plan_date || '') +
      (filter === 'all' ? '' : '-' + filterLabels[filter]) + '.csv';
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
    showToast('今日日程已导出');
  }

  function closeScheduleDetail() {
    $('schedule-modal').classList.add('hidden');
  }

  function renderTimeline() {
    var data = state.data || {};
    var timeline = data.timeline || [];
    var clock = clockText();
    var currentMinutes = timeToMinutes(clock);
    var signature = JSON.stringify([data.persona, timeline, clock.slice(0, 5)]);
    if (signature === renderState.timeline) return;
    renderState.timeline = signature;
    var root = $('timeline');
    if (!timeline.length) {
      root.innerHTML = '<div class="empty-timeline">暂无时间线</div>';
      return;
    }
    var html = [];
    timeline.forEach(function (item, index) {
      var start = Number(item.start_min) || 0;
      var end = Number(item.end_min) || 0;
      if (end <= start) return;
      var left = start / 1440 * 100;
      var width = (end - start) / 1440 * 100;
      var cat = categoryClass(item);
      var currentClass = currentMinutes >= start && currentMinutes < end
        ? ' current' : '';
      var label = width > 4.0 ? escapeHtml(item.location || item.activity) : '';
      var tip = (item.start || '') + '–' + (item.end || '') + ' · ' +
        (item.activity || '') + ' · ' + (item.location || '');
      html.push('<div class="timeline-segment ' + cat + currentClass +
        '" data-schedule-index="' + index + '" title="' + escapeHtml(tip) + '" style="left:' + left +
        '%;width:' + width + '%"><span>' + label + '</span></div>');
    });
    var markerLeft = Math.min(100, Math.max(0, currentMinutes / 1440 * 100));
    html.push('<div class="timeline-marker" style="left:' + markerLeft + '%"><span>' +
      escapeHtml(clock.slice(0, 5)) + '</span></div>');
    html.push('<div class="timeline-ticks">');
    [0, 360, 720, 1080, 1440].forEach(function (tick) {
      var text = tick === 1440 ? '24:00' : String(Math.floor(tick / 60)).padStart(2, '0') + ':00';
      html.push('<span style="left:' + (tick / 1440 * 100) + '%">' + text + '</span>');
    });
    html.push('</div>');
    root.innerHTML = html.join('');
    $('timeline-now').textContent = '现在 ' + clock.slice(0, 5);
    $('timeline-legend').innerHTML = [
      '<span><i class="dot home"></i>在家</span>',
      '<span><i class="dot outside"></i>外出</span>',
      '<span><i class="dot transit"></i>路上</span>',
      '<span><i class="dot sleep"></i>睡眠</span>'
    ].join('');
  }

  function renderScenePicker(force) {
    var data = state.data || {};
    var signature = pickerSignature(data);
    if (!force && signature === renderState.picker) return;
    renderState.picker = signature;
    var now = data.now || null;
    var picker = $('scene-picker');
    var chips = $('scene-chips');
    if (!now) {
      picker.classList.add('hidden');
      return;
    }
    picker.classList.remove('hidden');
    var actual = now.kind === 'home' ? null : sceneFor(now);
    var active = state.previewScene || actual;
    chips.innerHTML = SCENES.map(function (scene) {
      return '<button class="chip ' + (scene.key === active ? 'active' : '') +
        '" data-scene="' + scene.key + '"><span class="chip-icon">' +
        sceneIconSvg(scene.key) + '</span>' + scene.label + '</button>';
    }).join('');
    Array.prototype.forEach.call(chips.querySelectorAll('.chip'), function (chip) {
      chip.addEventListener('click', function () {
        var key = chip.getAttribute('data-scene');
        if (key === actual) {
          state.previewScene = null;
        } else {
          state.previewScene = key;
        }
        renderScene(true);
        renderScenePicker(true);
      });
    });
  }

