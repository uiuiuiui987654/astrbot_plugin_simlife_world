  // ---------------------------------------------------------------- 游戏机 · 多小游戏
  var GAME_MAX_HP = 60;
  var GAME_MAX_ROUNDS = 12;
  var GAME_MOVE_LABELS = { attack: '攻击', defend: '防御', special: '必杀' };
  var GAME_TAUNTS = {
    attack: ['就这？', '这一拳软绵绵的。', '你是在给我挠痒？', '力度还行，准头不行。'],
    defend: ['缩得倒挺快。', '就知道你会防。', '防吧，反正你也打不疼我。'],
    special: ['看招！', '这招你接得住吗？', '别眨眼。', '吃我这记必杀！']
  };
  var RPS_LABELS = { rock: '石头', scissors: '剪刀', paper: '布' };
  var gameState = {
    current: '',
    replyTimer: 0,
    battle: { playerHp: GAME_MAX_HP, aiHp: GAME_MAX_HP, round: 1, busy: false, playerCd: 0, aiCd: 0, over: false },
    rps: { player: 0, ai: 0, round: 1, busy: false, over: false },
    mole: { score: 0, aiScore: 0, timeLeft: 8, tickTimer: 0, spawnTimer: 0, endTimer: 0, active: false, over: false },
    ttt: { board: ['', '', '', '', '', '', '', '', ''], busy: false, over: false, timer: 0 },
    memory: { deck: [], flipped: [], matched: 0, moves: 0, aiMoves: 0, busy: false, over: false, timer: 0 },
    guess: { target: 0, attempts: 0, max: 7, over: false },
    dice: { player: 0, ai: 0, round: 1, busy: false, over: false },
    gomoku: { board: [], busy: false, over: false, timer: 0 },
    connect4: { board: [], busy: false, over: false, timer: 0 },
    reversi: { board: [], busy: false, over: false, timer: 0 },
    launchItem: 'game_console',
    launchAction: '打游戏'
  };

  function isGameConsole(item) {
    if (!item) return false;
    var id = String(item.id || '');
    var name = String(item.name || '');
    return id === 'game_console' || name.indexOf('游戏机') >= 0;
  }

  function isBoardGame(item) {
    if (!item) return false;
    var id = String(item.id || '');
    var name = String(item.name || '');
    return id === 'board_game' || name.indexOf('桌游') >= 0 || name.indexOf('拼图') >= 0;
  }

  function isGameItem(item) {
    return isGameConsole(item) || isBoardGame(item);
  }

  function stopTttTimer() {
    if (gameState.ttt.timer) {
      clearTimeout(gameState.ttt.timer);
      gameState.ttt.timer = 0;
    }
  }

  function stopMemoryTimer() {
    if (gameState.memory.timer) {
      clearTimeout(gameState.memory.timer);
      gameState.memory.timer = 0;
    }
  }

  function stopGomokuTimer() {
    if (gameState.gomoku.timer) {
      clearTimeout(gameState.gomoku.timer);
      gameState.gomoku.timer = 0;
    }
  }

  function stopConnect4Timer() {
    if (gameState.connect4.timer) {
      clearTimeout(gameState.connect4.timer);
      gameState.connect4.timer = 0;
    }
  }

  function stopReversiTimer() {
    if (gameState.reversi.timer) {
      clearTimeout(gameState.reversi.timer);
      gameState.reversi.timer = 0;
    }
  }

  function openGameModal() {
    if (!state.selectedItem || !isGameItem(state.selectedItem)) return;
    var boardMode = isBoardGame(state.selectedItem);
    gameState.launchItem = boardMode ? 'board_game' : 'game_console';
    gameState.launchAction = boardMode ? '开一局桌游' : '打一局';
    closeItem();
    clearGameReply();
    stopMoleTimers();
    stopTttTimer();
    stopMemoryTimer();
    stopGomokuTimer();
    stopConnect4Timer();
    stopReversiTimer();
    gameState.current = '';
    $('game-ai-reply').classList.add('hidden');
    $('game-ai-reply').textContent = '';
    $('game-restart').classList.add('hidden');
    $('game-play-step').classList.add('hidden');
    $('game-select-step').classList.remove('hidden');
    $('game-head-title').textContent = boardMode ? '桌游' : '游戏机';
    $('game-sub').textContent = boardMode
      ? '选一个桌游，和月月下一局'
      : '选一个小游戏，和月月打';
    document.querySelectorAll('#game-select-step .game-pick').forEach(function (button) {
      button.classList.toggle('hidden', boardMode && button.getAttribute('data-board') !== '1');
    });
    $('game-modal').classList.remove('hidden');
  }

  function closeGameModal() {
    clearGameReply();
    stopMoleTimers();
    stopTttTimer();
    stopMemoryTimer();
    stopGomokuTimer();
    stopConnect4Timer();
    stopReversiTimer();
    $('game-modal').classList.add('hidden');
  }

  function startGame(game) {
    if (['battle', 'rps', 'mole', 'ttt', 'memory', 'guess', 'dice', 'gomoku', 'connect4', 'reversi'].indexOf(game) < 0) return;
    clearGameReply();
    stopMoleTimers();
    stopTttTimer();
    stopMemoryTimer();
    stopGomokuTimer();
    stopConnect4Timer();
    stopReversiTimer();
    gameState.current = game;
    $('game-select-step').classList.add('hidden');
    $('game-play-step').classList.remove('hidden');
    $('game-restart').classList.add('hidden');
    $('game-ai-reply').classList.add('hidden');
    $('game-ai-reply').textContent = '';
    ['game-battle-step', 'game-rps-step', 'game-mole-step', 'game-ttt-step', 'game-memory-step', 'game-guess-step', 'game-dice-step', 'game-gomoku-step', 'game-connect4-step', 'game-reversi-step'].forEach(function (id) {
      $(id).classList.add('hidden');
    });
    if (game === 'battle') {
      $('game-battle-step').classList.remove('hidden');
      $('game-title').textContent = '街机对战';
      $('game-sub').textContent = '你 VS 月月';
      startBattle();
    } else if (game === 'rps') {
      $('game-rps-step').classList.remove('hidden');
      $('game-title').textContent = '猜拳';
      $('game-sub').textContent = '三局两胜';
      startRps();
    } else if (game === 'mole') {
      $('game-mole-step').classList.remove('hidden');
      $('game-title').textContent = '打地鼠';
      $('game-sub').textContent = '8 秒手速挑战';
      startMole();
    } else if (game === 'memory') {
      $('game-memory-step').classList.remove('hidden');
      $('game-title').textContent = '翻牌记忆';
      $('game-sub').textContent = '和月月比步数';
      startMemory();
    } else if (game === 'guess') {
      $('game-guess-step').classList.remove('hidden');
      $('game-title').textContent = '猜数字';
      $('game-sub').textContent = '1–100，7 次机会';
      startGuess();
    } else if (game === 'dice') {
      $('game-dice-step').classList.remove('hidden');
      $('game-title').textContent = '比大小';
      $('game-sub').textContent = '三局两胜掷骰子';
      startDice();
    } else if (game === 'gomoku') {
      $('game-gomoku-step').classList.remove('hidden');
      $('game-title').textContent = '五子棋';
      $('game-sub').textContent = '15×15 连成五子';
      startGomoku();
    } else if (game === 'connect4') {
      $('game-connect4-step').classList.remove('hidden');
      $('game-title').textContent = '四子棋';
      $('game-sub').textContent = '7×6 连成四子';
      startConnect4();
    } else if (game === 'reversi') {
      $('game-reversi-step').classList.remove('hidden');
      $('game-title').textContent = '黑白棋';
      $('game-sub').textContent = '8×8 翻子比多少';
      startReversi();
    } else {
      $('game-ttt-step').classList.remove('hidden');
      $('game-title').textContent = '井字棋';
      $('game-sub').textContent = '你执 X，月月执 O';
      startTtt();
    }
  }

  function restartCurrentGame() {
    if (!gameState.current) return;
    startGame(gameState.current);
  }

  function leaveGame() {
    clearGameReply();
    stopMoleTimers();
    stopTttTimer();
    stopMemoryTimer();
    stopGomokuTimer();
    stopConnect4Timer();
    stopReversiTimer();
    gameState.current = '';
    $('game-play-step').classList.add('hidden');
    $('game-select-step').classList.remove('hidden');
    $('game-restart').classList.add('hidden');
    $('game-ai-reply').classList.add('hidden');
    $('game-ai-reply').textContent = '';
    $('game-sub').textContent = isBoardGame(state.selectedItem)
      ? '选一个桌游，和月月下一局'
      : '选一个小游戏，和月月打';
  }

  function gameResultNode() {
    if (gameState.current === 'battle') return $('game-log');
    if (gameState.current === 'rps') return $('game-rps-log');
    if (gameState.current === 'mole') return $('game-mole-status');
    if (gameState.current === 'ttt') return $('game-ttt-status');
    if (gameState.current === 'memory') return $('game-memory-status');
    if (gameState.current === 'guess') return $('game-guess-status');
    if (gameState.current === 'dice') return $('game-dice-status');
    if (gameState.current === 'gomoku') return $('game-gomoku-status');
    if (gameState.current === 'connect4') return $('game-connect4-status');
    if (gameState.current === 'reversi') return $('game-reversi-status');
    return $('game-log');
  }

  function appendGameResult(text) {
    var node = gameResultNode();
    node.textContent = text;
  }

  function showGameResult(summary, chat, gameMeta) {
    $('game-restart').classList.remove('hidden');
    appendGameResult(summary);
    sendGameChat(chat, gameMeta || null, summary);
  }

  function showGameReply(text) {
    var node = $('game-ai-reply');
    node.textContent = text;
    node.classList.remove('hidden');
  }

  function clearGameReply() {
    if (gameState.replyTimer) {
      clearTimeout(gameState.replyTimer);
      gameState.replyTimer = 0;
    }
  }

  function sendGameChat(text, gameMeta, summary) {
    clearGameReply();
    showGameReply('她放下手柄，正在回你……');
    var gameItem = gameState.launchItem || 'game_console';
    var gameAction = gameState.launchAction || '打游戏';
    var payload = {
      kind: 'chat',
      item_id: gameItem,
      action: gameAction,
      text: text
    };
    if (gameMeta) {
      payload = {
        kind: 'game',
        item_id: gameItem,
        action: gameAction,
        text: '',
        game_name: gameMeta.name || '小游戏',
        game_result: gameMeta.result || '',
        game_score: gameMeta.score || '',
        game_summary: summary || ''
      };
    }
    fetch('/api/interact', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })
      .then(function (response) { return response.json(); })
      .then(function (data) {
        if (!data.ok) throw new Error(data.error || '呼叫失败');
        pollGameReply(data.id, Date.now());
      })
      .catch(function (error) {
        showGameReply('她没应声：' + error.message);
      });
  }

  function pollGameReply(id, startedAt) {
    gameState.replyTimer = window.setTimeout(function () {
      fetch('/api/interact?id=' + encodeURIComponent(id), { cache: 'no-store' })
        .then(function (response) { return response.json(); })
        .then(function (data) {
          if (!data.ok) throw new Error(data.error || '读取失败');
          if (data.pending) {
            if (Date.now() - startedAt > 45000) throw new Error('她好像没听见');
            pollGameReply(id, startedAt);
            return;
          }
          var reply = data.response || {};
          showGameReply(reply.speech || reply.reply || reply.text || '她哼了一声。');
          clearGameReply();
        })
        .catch(function (error) {
          showGameReply('她没应声：' + error.message);
          clearGameReply();
        });
    }, 1200);
  }

  // ---------------------------------------------------------- 街机对战
  function startBattle() {
    var battle = gameState.battle;
    battle.playerHp = GAME_MAX_HP;
    battle.aiHp = GAME_MAX_HP;
    battle.round = 1;
    battle.busy = false;
    battle.playerCd = 0;
    battle.aiCd = 0;
    battle.over = false;
    $('game-log').textContent = '选一个招式，开打。';
    updateBattleHud();
    setBattleButtons(true);
  }

  function setBattleButtons(enabled) {
    Array.prototype.forEach.call(document.querySelectorAll('#game-battle-step .game-move'), function (button) {
      var move = button.getAttribute('data-move');
      button.disabled = !enabled || (move === 'special' && gameState.battle.playerCd > 0);
    });
  }

  function updateBattleHud() {
    var battle = gameState.battle;
    var playerFill = $('game-hp-player');
    var aiFill = $('game-hp-ai');
    if (playerFill) playerFill.style.width = (battle.playerHp / GAME_MAX_HP * 100) + '%';
    if (aiFill) aiFill.style.width = (battle.aiHp / GAME_MAX_HP * 100) + '%';
    $('game-hp-player-text').textContent = battle.playerHp + ' / ' + GAME_MAX_HP;
    $('game-hp-ai-text').textContent = battle.aiHp + ' / ' + GAME_MAX_HP;
    $('game-round').textContent = battle.over ? '对战结束' : '第 ' + battle.round + ' 回合';
    var special = document.querySelector('#game-battle-step .game-move[data-move="special"]');
    if (special) {
      special.innerHTML = battle.playerCd > 0
        ? '必杀<small>冷却 ' + battle.playerCd + ' 回合</small>'
        : '必杀<small>冷却 2 回合</small>';
    }
  }

  function appendBattleLog(text) {
    var log = $('game-log');
    log.textContent = (log.textContent ? log.textContent + '\n' : '') + text;
    log.scrollTop = log.scrollHeight;
  }

  function pickBattleAiMove() {
    var battle = gameState.battle;
    var roll = Math.random();
    if (battle.aiCd <= 0 && (battle.playerHp <= 22 || roll < 0.16)) return 'special';
    if (battle.aiHp <= 18 && roll < 0.45) return 'defend';
    if (roll < 0.58) return 'attack';
    if (roll < 0.86) return 'defend';
    return 'attack';
  }

  function battleMoveDamage(move) {
    if (move === 'attack') return 8 + Math.floor(Math.random() * 6);
    if (move === 'special') return 16 + Math.floor(Math.random() * 7);
    return 0;
  }

  function battleTaunt(move) {
    var list = GAME_TAUNTS[move] || GAME_TAUNTS.attack;
    return list[Math.floor(Math.random() * list.length)];
  }

  function chooseBattleMove(move) {
    var battle = gameState.battle;
    if (battle.busy || battle.over) return;
    if (move === 'special' && battle.playerCd > 0) return;
    battle.busy = true;
    setBattleButtons(false);
    appendBattleLog('你：' + GAME_MOVE_LABELS[move] + '！');
    appendBattleLog('月月正在选招式……');
    var aiMove = pickBattleAiMove();
    window.setTimeout(function () {
      resolveBattleTurn(move, aiMove);
    }, 480);
  }

  function resolveBattleTurn(playerMove, aiMove) {
    var battle = gameState.battle;
    var playerDamage = 0;
    var aiDamage = 0;
    if (playerMove !== 'defend') {
      playerDamage = battleMoveDamage(playerMove);
      if (aiMove === 'defend') playerDamage = Math.max(1, Math.round(playerDamage * 0.3));
      if (playerMove === 'special') battle.playerCd = 2;
    }
    if (aiMove !== 'defend') {
      aiDamage = battleMoveDamage(aiMove);
      if (playerMove === 'defend') aiDamage = Math.max(1, Math.round(aiDamage * 0.25));
      if (aiMove === 'special') battle.aiCd = 2;
    }
    battle.aiHp = Math.max(0, battle.aiHp - playerDamage);
    battle.playerHp = Math.max(0, battle.playerHp - aiDamage);
    var lines = ['月月：' + GAME_MOVE_LABELS[aiMove] + '！'];
    if (playerDamage > 0) lines.push('你对月月造成 ' + playerDamage + ' 点伤害。');
    else if (playerMove === 'defend') lines.push('你摆出防御姿态。');
    if (aiDamage > 0) lines.push('月月对你造成 ' + aiDamage + ' 点伤害。');
    else if (aiMove === 'defend') lines.push('月月选择了防御。');
    if (aiMove !== 'defend' && Math.random() < 0.55) lines.push('月月：' + battleTaunt(aiMove));
    if (battle.playerCd > 0) battle.playerCd -= 1;
    if (battle.aiCd > 0) battle.aiCd -= 1;
    appendBattleLog(lines.join('\n'));
    updateBattleHud();
    if (battle.playerHp <= 0 || battle.aiHp <= 0 || battle.round >= GAME_MAX_ROUNDS) {
      finishBattle();
      return;
    }
    battle.round += 1;
    battle.busy = false;
    updateBattleHud();
    setBattleButtons(true);
  }

  function finishBattle() {
    var battle = gameState.battle;
    battle.over = true;
    battle.busy = false;
    setBattleButtons(false);
    updateBattleHud();
    var result;
    if (battle.playerHp <= 0 && battle.aiHp <= 0) result = 'draw';
    else if (battle.aiHp <= 0) result = 'win';
    else if (battle.playerHp <= 0) result = 'lose';
    else result = battle.playerHp === battle.aiHp ? 'draw' : battle.playerHp > battle.aiHp ? 'win' : 'lose';
    var summary;
    var chat;
    if (result === 'win') {
      summary = '你赢了！月月还剩 ' + battle.aiHp + ' 点血。';
      chat = '刚刚跟你打街机，我赢了，你只剩 ' + battle.aiHp + ' 血，服不服？';
    } else if (result === 'lose') {
      summary = '月月赢了。你还剩 ' + battle.playerHp + ' 点血。';
      chat = '刚刚跟你打街机我输了，我还剩 ' + battle.playerHp + ' 血，下次再来。';
    } else {
      summary = '平局，谁也没服谁。';
      chat = '刚刚跟你打街机打成平手，谁也没赢，再来一局？';
    }
    appendBattleLog('\n' + summary);
    showGameResult(summary, chat, {
      name: '街机对战',
      result: result,
      score: battle.playerHp + ':' + battle.aiHp
    });
  }

  // ---------------------------------------------------------- 猜拳
  function startRps() {
    var rps = gameState.rps;
    rps.player = 0;
    rps.ai = 0;
    rps.round = 1;
    rps.busy = false;
    rps.over = false;
    $('game-rps-player').textContent = '0';
    $('game-rps-ai').textContent = '0';
    $('game-rps-round').textContent = '第 1 局';
    $('game-rps-log').textContent = '选石头、剪刀或布。';
    setRpsButtons(true);
  }

  function setRpsButtons(enabled) {
    Array.prototype.forEach.call(document.querySelectorAll('#game-rps-step [data-rps]'), function (button) {
      button.disabled = !enabled;
    });
  }

  function chooseRps(choice) {
    var rps = gameState.rps;
    if (rps.busy || rps.over) return;
    rps.busy = true;
    setRpsButtons(false);
    var choices = ['rock', 'paper', 'scissors'];
    var aiChoice = choices[Math.floor(Math.random() * choices.length)];
    var playerLabel = RPS_LABELS[choice];
    var aiLabel = RPS_LABELS[aiChoice];
    var result;
    if (choice === aiChoice) {
      result = 'draw';
    } else if (
      (choice === 'rock' && aiChoice === 'scissors') ||
      (choice === 'scissors' && aiChoice === 'paper') ||
      (choice === 'paper' && aiChoice === 'rock')
    ) {
      result = 'player';
    } else {
      result = 'ai';
    }
    if (result === 'player') {
      rps.player += 1;
      $('game-rps-player').textContent = String(rps.player);
    } else if (result === 'ai') {
      rps.ai += 1;
      $('game-rps-ai').textContent = String(rps.ai);
    }
    $('game-rps-round').textContent = '第 ' + rps.round + ' 局';
    var line = '你出' + playerLabel + '，月月出' + aiLabel + '。' +
      (result === 'draw' ? '平局。' : result === 'player' ? '你赢一局。' : '月月赢一局。');

    if (rps.player >= 2 || rps.ai >= 2) {
      rps.over = true;
      rps.busy = false;
      var win = rps.player >= 2;
      var summary = win ? '你赢了！最终比分 ' + rps.player + ' : ' + rps.ai + '。'
        : '月月赢了，最终比分 ' + rps.player + ' : ' + rps.ai + '。';
      var chat = win ? '刚刚跟你猜拳我赢了，最终 ' + rps.player + ' : ' + rps.ai + '，服不服？'
        : '刚刚跟你猜拳我输了，最终 ' + rps.ai + ' : ' + rps.player + '，再来一局？';
      $('game-rps-log').textContent = line + '\n' + summary;
      showGameResult(summary, chat, {
        name: '猜拳',
        result: win ? 'win' : 'lose',
        score: rps.player + ':' + rps.ai
      });
      return;
    }
    rps.round += 1;
    rps.busy = false;
    $('game-rps-log').textContent = line;
    $('game-rps-round').textContent = '第 ' + rps.round + ' 局';
    setRpsButtons(true);
  }

  // ---------------------------------------------------------- 打地鼠
  function startMole() {
    var mole = gameState.mole;
    stopMoleTimers();
    mole.score = 0;
    mole.aiScore = 5 + Math.floor(Math.random() * 5);
    mole.timeLeft = 8;
    mole.active = false;
    mole.over = false;
    $('game-mole-player').textContent = '0';
    $('game-mole-ai').textContent = String(mole.aiScore);
    $('game-mole-time').textContent = '8.0s';
    $('game-mole-status').textContent = '准备打地鼠，月月已经准备好了。';
    $('game-mole-start').classList.remove('hidden');
    $('game-mole-start').disabled = false;
    renderMoleGrid();
  }

  function renderMoleGrid() {
    var grid = $('game-mole-grid');
    grid.innerHTML = '';
    for (var i = 0; i < 9; i++) {
      var button = document.createElement('button');
      button.type = 'button';
      button.className = 'game-mole-cell';
      button.setAttribute('data-cell', String(i));
      grid.appendChild(button);
    }
  }

  function stopMoleTimers() {
    var mole = gameState.mole;
    if (mole.tickTimer) clearInterval(mole.tickTimer);
    if (mole.spawnTimer) clearInterval(mole.spawnTimer);
    if (mole.endTimer) clearTimeout(mole.endTimer);
    mole.tickTimer = 0;
    mole.spawnTimer = 0;
    mole.endTimer = 0;
  }

  function startMoleRound() {
    var mole = gameState.mole;
    if (mole.active || mole.over) return;
    stopMoleTimers();
    mole.active = true;
    mole.score = 0;
    mole.timeLeft = 8;
    $('game-mole-player').textContent = '0';
    $('game-mole-status').textContent = '开始！快打地鼠。';
    $('game-mole-start').classList.add('hidden');
    spawnMole();
    mole.spawnTimer = window.setInterval(spawnMole, 650);
    mole.tickTimer = window.setInterval(function () {
      mole.timeLeft = Math.max(0, mole.timeLeft - 0.1);
      $('game-mole-time').textContent = mole.timeLeft.toFixed(1) + 's';
    }, 100);
    mole.endTimer = window.setTimeout(endMoleRound, 8000);
  }

  function spawnMole() {
    var mole = gameState.mole;
    if (!mole.active) return;
    Array.prototype.forEach.call(document.querySelectorAll('.game-mole-cell'), function (button) {
      button.classList.remove('active');
      button.textContent = '';
    });
    var cells = document.querySelectorAll('.game-mole-cell');
    if (!cells.length) return;
    var target = cells[Math.floor(Math.random() * cells.length)];
    target.classList.add('active');
    target.textContent = '🐹';
  }

  function hitMole(event) {
    var mole = gameState.mole;
    if (!mole.active) return;
    var cell = event.target.closest('.game-mole-cell');
    if (!cell || !cell.classList.contains('active')) return;
    mole.score += 1;
    $('game-mole-player').textContent = String(mole.score);
    spawnMole();
  }

  function endMoleRound() {
    var mole = gameState.mole;
    if (!mole.active) return;
    mole.active = false;
    stopMoleTimers();
    Array.prototype.forEach.call(document.querySelectorAll('.game-mole-cell'), function (button) {
      button.classList.remove('active');
      button.textContent = '';
    });
    mole.over = true;
    var win = mole.score > mole.aiScore;
    var draw = mole.score === mole.aiScore;
    var summary = win ? '你赢了！你打了 ' + mole.score + ' 只，月月打了 ' + mole.aiScore + ' 只。'
      : draw ? '平局，你们都打了 ' + mole.score + ' 只。'
        : '月月赢了。你打了 ' + mole.score + ' 只，月月打了 ' + mole.aiScore + ' 只。';
    var chat = win ? '刚刚跟你打地鼠我赢了，我打了 ' + mole.score + ' 只，你才 ' + mole.aiScore + ' 只。'
      : draw ? '刚刚跟你打地鼠打成平手，都打了 ' + mole.score + ' 只，再来？'
        : '刚刚跟你打地鼠我输了，你打了 ' + mole.aiScore + ' 只，我只有 ' + mole.score + ' 只。';
    $('game-mole-status').textContent = summary;
    showGameResult(summary, chat, {
      name: '打地鼠',
      result: win ? 'win' : draw ? 'draw' : 'lose',
      score: mole.score + ':' + mole.aiScore
    });
  }

  // ---------------------------------------------------------- 井字棋
  var TTT_LINES = [
    [0, 1, 2], [3, 4, 5], [6, 7, 8],
    [0, 3, 6], [1, 4, 7], [2, 5, 8],
    [0, 4, 8], [2, 4, 6]
  ];

  function startTtt() {
    var ttt = gameState.ttt;
    if (ttt.timer) {
      clearTimeout(ttt.timer);
      ttt.timer = 0;
    }
    ttt.board = ['', '', '', '', '', '', '', '', ''];
    ttt.busy = false;
    ttt.over = false;
    renderTtt();
    $('game-ttt-status').textContent = '你执 X，月月执 O，你先手。';
    setTttButtons(true);
  }

  function renderTtt() {
    var board = $('game-ttt-board');
    board.innerHTML = '';
    for (var i = 0; i < 9; i++) {
      var button = document.createElement('button');
      button.type = 'button';
      button.className = 'game-ttt-cell' + (gameState.ttt.board[i] ? ' filled' : '');
      button.setAttribute('data-cell', String(i));
      button.textContent = gameState.ttt.board[i];
      board.appendChild(button);
    }
  }

  function setTttButtons(enabled) {
    Array.prototype.forEach.call(document.querySelectorAll('.game-ttt-cell'), function (button) {
      button.disabled = !enabled || Boolean(gameState.ttt.board[Number(button.getAttribute('data-cell'))]);
    });
  }

  function findTttWinner(mark) {
    for (var i = 0; i < TTT_LINES.length; i++) {
      var line = TTT_LINES[i];
      if (
        gameState.ttt.board[line[0]] === mark &&
        gameState.ttt.board[line[1]] === mark &&
        gameState.ttt.board[line[2]] === mark
      ) {
        return true;
      }
    }
    return false;
  }

  function tttBoardFull() {
    for (var i = 0; i < 9; i++) {
      if (!gameState.ttt.board[i]) return false;
    }
    return true;
  }

  function tttPlayerMove(index) {
    var ttt = gameState.ttt;
    if (ttt.busy || ttt.over || ttt.board[index]) return;
    ttt.board[index] = 'X';
    renderTtt();
    if (findTttWinner('X')) {
      finishTtt('win');
      return;
    }
    if (tttBoardFull()) {
      finishTtt('draw');
      return;
    }
    ttt.busy = true;
    $('game-ttt-status').textContent = '月月正在想……';
    ttt.timer = window.setTimeout(function () {
      tttAiMove();
    }, 380);
  }

  function tttAiMove() {
    var ttt = gameState.ttt;
    if (ttt.over) return;
    var move = pickTttMove();
    if (move < 0) {
      ttt.busy = false;
      return;
    }
    ttt.board[move] = 'O';
    renderTtt();
    if (findTttWinner('O')) {
      finishTtt('lose');
      return;
    }
    if (tttBoardFull()) {
      finishTtt('draw');
      return;
    }
    ttt.busy = false;
    setTttButtons(true);
    $('game-ttt-status').textContent = '轮到你落子。';
  }

  function pickTttMove() {
    var board = gameState.ttt.board;
    var i;
    var empty = [];
    for (i = 0; i < 9; i++) if (board[i] === '') empty.push(i);
    if (!empty.length) return -1;
    // 月月偶尔走神，给玩家留出赢棋机会。
    if (Math.random() < 0.42) {
      return empty[Math.floor(Math.random() * empty.length)];
    }
    for (i = 0; i < 9; i++) if (board[i] === '') { board[i] = 'O'; if (findTttWinner('O')) { board[i] = ''; return i; } board[i] = ''; }
    for (i = 0; i < 9; i++) if (board[i] === '') { board[i] = 'X'; if (findTttWinner('X')) { board[i] = ''; return i; } board[i] = ''; }
    if (board[4] === '') return 4;
    var corners = [0, 2, 6, 8].filter(function (index) { return board[index] === ''; });
    if (corners.length) return corners[Math.floor(Math.random() * corners.length)];
    return empty[Math.floor(Math.random() * empty.length)];
  }

  function finishTtt(result) {
    var ttt = gameState.ttt;
    ttt.over = true;
    ttt.busy = false;
    if (ttt.timer) {
      clearTimeout(ttt.timer);
      ttt.timer = 0;
    }
    renderTtt();
    setTttButtons(false);
    var summary;
    var chat;
    if (result === 'win') {
      summary = '你赢了！你连成一线了。';
      chat = '刚刚跟你下井字棋我赢了，我连成一线了，再来一局？';
    } else if (result === 'lose') {
      summary = '月月赢了，她连成一线了。';
      chat = '刚刚跟你下井字棋我输了，你连成一线了，再来一局？';
    } else {
      summary = '平局，棋盘满了，谁也没连成线。';
      chat = '刚刚跟你下井字棋打成平手，棋盘满了，再来一局？';
    }
    $('game-ttt-status').textContent = summary;
    showGameResult(summary, chat, {
      name: '井字棋',
      result: result,
      score: ''
    });
  }

  // ---------------------------------------------------------- 翻牌记忆
  var MEMORY_SYMBOLS = ['🐳', '🐟', '🦊', '🍙', '🎮', '🍰'];

  function startMemory() {
    var memory = gameState.memory;
    stopMemoryTimer();
    memory.deck = [];
    MEMORY_SYMBOLS.concat(MEMORY_SYMBOLS).forEach(function (symbol) {
      memory.deck.push({ symbol: symbol, faceUp: false, matched: false });
    });
    for (var i = memory.deck.length - 1; i > 0; i--) {
      var j = Math.floor(Math.random() * (i + 1));
      var tmp = memory.deck[i];
      memory.deck[i] = memory.deck[j];
      memory.deck[j] = tmp;
    }
    memory.flipped = [];
    memory.matched = 0;
    memory.moves = 0;
    memory.aiMoves = 7 + Math.floor(Math.random() * 4);
    memory.busy = false;
    memory.over = false;
    $('game-memory-moves').textContent = '0';
    $('game-memory-ai').textContent = String(memory.aiMoves);
    $('game-memory-status').textContent = '点开两张牌，找出相同图案。月月说 ' + memory.aiMoves + ' 步内能完成。';
    renderMemoryGrid();
  }

  function renderMemoryGrid() {
    var grid = $('game-memory-grid');
    grid.innerHTML = '';
    gameState.memory.deck.forEach(function (card, index) {
      var button = document.createElement('button');
      button.type = 'button';
      button.className = 'game-memory-card' +
        (card.faceUp || card.matched ? ' flipped' : '') +
        (card.matched ? ' matched' : '');
      button.setAttribute('data-index', String(index));
      button.textContent = card.faceUp || card.matched ? card.symbol : '?';
      button.disabled = card.matched;
      grid.appendChild(button);
    });
  }

  function memoryClick(index) {
    var memory = gameState.memory;
    if (memory.busy || memory.over) return;
    var card = memory.deck[index];
    if (!card || card.faceUp || card.matched) return;
    card.faceUp = true;
    memory.flipped.push(index);
    renderMemoryGrid();
    if (memory.flipped.length < 2) return;
    memory.moves += 1;
    $('game-memory-moves').textContent = String(memory.moves);
    var first = memory.flipped[0];
    var second = memory.flipped[1];
    if (memory.deck[first].symbol === memory.deck[second].symbol) {
      memory.deck[first].matched = true;
      memory.deck[second].matched = true;
      memory.matched += 2;
      memory.flipped = [];
      memory.busy = false;
      renderMemoryGrid();
      if (memory.matched >= memory.deck.length) {
        finishMemory();
      } else {
        $('game-memory-status').textContent = '配对成功，继续。';
      }
      return;
    }
    memory.busy = true;
    memory.timer = window.setTimeout(function () {
      memory.deck[first].faceUp = false;
      memory.deck[second].faceUp = false;
      memory.flipped = [];
      memory.busy = false;
      memory.timer = 0;
      renderMemoryGrid();
      $('game-memory-status').textContent = '没配上，再试试。';
    }, 700);
  }

  function finishMemory() {
    var memory = gameState.memory;
    memory.over = true;
    memory.busy = false;
    var win = memory.moves <= memory.aiMoves;
    var summary = win
      ? '你赢了！你用了 ' + memory.moves + ' 步，月月目标 ' + memory.aiMoves + ' 步。'
      : '月月赢了。你用了 ' + memory.moves + ' 步，超过她的 ' + memory.aiMoves + ' 步。';
    var chat = win
      ? '刚刚跟你玩翻牌记忆我赢了，我 ' + memory.moves + ' 步就翻完了，还挺快。'
      : '刚刚跟你玩翻牌记忆我输了，我用了 ' + memory.moves + ' 步，你给的目标是 ' + memory.aiMoves + ' 步。';
    $('game-memory-status').textContent = summary;
    showGameResult(summary, chat, {
      name: '翻牌记忆',
      result: win ? 'win' : 'lose',
      score: memory.moves + ':' + memory.aiMoves
    });
  }

  // ---------------------------------------------------------- 猜数字
  function startGuess() {
    var guess = gameState.guess;
    guess.target = 1 + Math.floor(Math.random() * 100);
    guess.attempts = 0;
    guess.over = false;
    $('game-guess-input').disabled = false;
    $('game-guess-submit').disabled = false;
    $('game-guess-input').value = '';
    $('game-guess-range').textContent = '范围 1 – 100';
    $('game-guess-status').textContent = '月月想好数字了，你猜。还剩 7 次机会。';
    window.setTimeout(function () {
      var input = $('game-guess-input');
      if (input) input.focus();
    }, 60);
  }

  function submitGuess() {
    var guess = gameState.guess;
    if (guess.over) return;
    var input = $('game-guess-input');
    var value = Number(input.value);
    if (!Number.isInteger(value) || value < 1 || value > 100) {
      $('game-guess-status').textContent = '请输入 1–100 的整数。';
      return;
    }
    guess.attempts += 1;
    input.value = '';
    if (value === guess.target) {
      finishGuess(true);
      return;
    }
    if (guess.attempts >= guess.max) {
      finishGuess(false);
      return;
    }
    var hint = value < guess.target ? '小了' : '大了';
    $('game-guess-range').textContent = '范围 1 – 100';
    $('game-guess-status').textContent =
      '你猜 ' + value + '，' + hint + '。还剩 ' + (guess.max - guess.attempts) + ' 次机会。';
    input.focus();
  }

  function finishGuess(win) {
    var guess = gameState.guess;
    guess.over = true;
    $('game-guess-input').disabled = true;
    $('game-guess-submit').disabled = true;
    var summary;
    var chat;
    if (win) {
      summary = '猜中了！答案是 ' + guess.target + '，你用了 ' + guess.attempts + ' 次。';
      chat = '刚刚跟你玩猜数字，你选的 ' + guess.target + ' 被我 ' + guess.attempts + ' 次就猜中了，运气不错。';
    } else {
      summary = '没猜中。月月选的数字是 ' + guess.target + '，7 次机会用完了。';
      chat = '刚刚跟你玩猜数字我输了，你选的 ' + guess.target + ' 我 7 次都没猜到，下次再练练。';
    }
    $('game-guess-status').textContent = summary;
    showGameResult(summary, chat, {
      name: '猜数字',
      result: win ? 'win' : 'lose',
      score: guess.attempts + ' 次'
    });
  }

  // ---------------------------------------------------------- 比大小
  function startDice() {
    var dice = gameState.dice;
    dice.player = 0;
    dice.ai = 0;
    dice.round = 1;
    dice.busy = false;
    dice.over = false;
    $('game-dice-player').textContent = '0';
    $('game-dice-ai').textContent = '0';
    $('game-dice-player-face').textContent = '?';
    $('game-dice-ai-face').textContent = '?';
    $('game-dice-round').textContent = '第 1 局';
    $('game-dice-status').textContent = '掷骰子比大小，三局两胜。';
    $('game-dice-roll').disabled = false;
  }

  function rollDice() {
    var dice = gameState.dice;
    if (dice.busy || dice.over) return;
    dice.busy = true;
    $('game-dice-roll').disabled = true;
    var playerRoll = 1 + Math.floor(Math.random() * 6);
    var aiRoll = 1 + Math.floor(Math.random() * 6);
    $('game-dice-player-face').textContent = String(playerRoll);
    $('game-dice-ai-face').textContent = String(aiRoll);
    var line;
    if (playerRoll > aiRoll) {
      dice.player += 1;
      line = '你掷出 ' + playerRoll + '，月月掷出 ' + aiRoll + '，你赢一局。';
    } else if (playerRoll < aiRoll) {
      dice.ai += 1;
      line = '你掷出 ' + playerRoll + '，月月掷出 ' + aiRoll + '，月月赢一局。';
    } else {
      line = '都是 ' + playerRoll + ' 点，平局，重掷。';
    }
    $('game-dice-player').textContent = String(dice.player);
    $('game-dice-ai').textContent = String(dice.ai);
    if (dice.player >= 2 || dice.ai >= 2) {
      dice.over = true;
      dice.busy = false;
      var win = dice.player >= 2;
      var summary = win
        ? '你赢了！最终比分 ' + dice.player + ' : ' + dice.ai + '。'
        : '月月赢了，最终比分 ' + dice.player + ' : ' + dice.ai + '。';
      var chat = win
        ? '刚刚跟你掷骰子我赢了，比分 ' + dice.player + ' : ' + dice.ai + '，运气也是实力。'
        : '刚刚跟你掷骰子我输了，比分 ' + dice.ai + ' : ' + dice.player + '，你运气不错。';
      $('game-dice-status').textContent = line + '\n' + summary;
      showGameResult(summary, chat, {
        name: '比大小',
        result: win ? 'win' : 'lose',
        score: dice.player + ':' + dice.ai
      });
      return;
    }
    dice.round += 1;
    dice.busy = false;
    $('game-dice-round').textContent = '第 ' + dice.round + ' 局';
    $('game-dice-status').textContent = line;
    $('game-dice-roll').disabled = false;
  }

  // ---------------------------------------------------------- 五子棋
  var GOMOKU_SIZE = 15;
  var GOMOKU_DIRS = [[1, 0], [0, 1], [1, 1], [1, -1]];

  function startGomoku() {
    var gomoku = gameState.gomoku;
    stopGomokuTimer();
    gomoku.board = [];
    for (var i = 0; i < GOMOKU_SIZE * GOMOKU_SIZE; i++) gomoku.board.push('');
    gomoku.busy = false;
    gomoku.over = false;
    renderGomoku();
    $('game-gomoku-status').textContent = '你执 X，月月执 O，你先手。';
  }

  function renderGomoku() {
    var board = $('game-gomoku-board');
    board.innerHTML = '';
    for (var i = 0; i < GOMOKU_SIZE * GOMOKU_SIZE; i++) {
      var button = document.createElement('button');
      var value = gameState.gomoku.board[i];
      button.type = 'button';
      button.className = 'game-gomoku-cell' +
        (value === 'X' ? ' x' : value === 'O' ? ' o' : '') +
        (value ? ' filled' : '');
      button.setAttribute('data-index', String(i));
      button.textContent = value;
      board.appendChild(button);
    }
  }

  function gomokuInside(x, y) {
    return x >= 0 && x < GOMOKU_SIZE && y >= 0 && y < GOMOKU_SIZE;
  }

  function gomokuWinner(index, mark) {
    var board = gameState.gomoku.board;
    var x = index % GOMOKU_SIZE;
    var y = Math.floor(index / GOMOKU_SIZE);
    for (var d = 0; d < GOMOKU_DIRS.length; d++) {
      var dx = GOMOKU_DIRS[d][0];
      var dy = GOMOKU_DIRS[d][1];
      var count = 1;
      for (var sign = -1; sign <= 1; sign += 2) {
        var nx = x + dx * sign;
        var ny = y + dy * sign;
        while (gomokuInside(nx, ny) && board[ny * GOMOKU_SIZE + nx] === mark) {
          count += 1;
          nx += dx * sign;
          ny += dy * sign;
        }
      }
      if (count >= 5) return true;
    }
    return false;
  }

  function gomokuBoardFull() {
    return gameState.gomoku.board.every(function (cell) { return Boolean(cell); });
  }

  function gomokuPlayerMove(index) {
    var gomoku = gameState.gomoku;
    if (gomoku.busy || gomoku.over || gomoku.board[index]) return;
    gomoku.board[index] = 'X';
    renderGomoku();
    if (gomokuWinner(index, 'X')) {
      finishGomoku('win');
      return;
    }
    if (gomokuBoardFull()) {
      finishGomoku('draw');
      return;
    }
    gomoku.busy = true;
    $('game-gomoku-status').textContent = '月月正在落子……';
    gomoku.timer = window.setTimeout(gomokuAiMove, 380);
  }

  function gomokuPotential(index, mark) {
    var board = gameState.gomoku.board;
    var x = index % GOMOKU_SIZE;
    var y = Math.floor(index / GOMOKU_SIZE);
    var total = 0;
    for (var d = 0; d < GOMOKU_DIRS.length; d++) {
      var dx = GOMOKU_DIRS[d][0];
      var dy = GOMOKU_DIRS[d][1];
      var count = 1;
      var openEnds = 0;
      for (var sign = -1; sign <= 1; sign += 2) {
        var nx = x + dx * sign;
        var ny = y + dy * sign;
        while (gomokuInside(nx, ny) && board[ny * GOMOKU_SIZE + nx] === mark) {
          count += 1;
          nx += dx * sign;
          ny += dy * sign;
        }
        if (gomokuInside(nx, ny) && board[ny * GOMOKU_SIZE + nx] === '') {
          openEnds += 1;
        }
      }
      if (count >= 5) return 1000000000;
      if (count === 4) total += openEnds >= 2 ? 3000000 : openEnds === 1 ? 300000 : 0;
      else if (count === 3) total += openEnds >= 2 ? 60000 : openEnds === 1 ? 6000 : 0;
      else if (count === 2) total += openEnds >= 2 ? 1200 : openEnds === 1 ? 160 : 0;
    }
    return total;
  }

  function gomokuCandidates() {
    var board = gameState.gomoku.board;
    var candidates = [];
    var hasStone = false;
    for (var i = 0; i < board.length; i++) {
      if (board[i]) {
        hasStone = true;
        break;
      }
    }
    if (!hasStone) return [Math.floor(GOMOKU_SIZE * GOMOKU_SIZE / 2)];
    for (var index = 0; index < board.length; index++) {
      if (board[index]) continue;
      var x = index % GOMOKU_SIZE;
      var y = Math.floor(index / GOMOKU_SIZE);
      var near = false;
      for (var dy = -2; dy <= 2 && !near; dy++) {
        for (var dx = -2; dx <= 2; dx++) {
          var nx = x + dx;
          var ny = y + dy;
          if (!gomokuInside(nx, ny)) continue;
          if (board[ny * GOMOKU_SIZE + nx]) {
            near = true;
            break;
          }
        }
      }
      if (near) candidates.push(index);
    }
    return candidates;
  }

  function pickGomokuMove() {
    var board = gameState.gomoku.board;
    var candidates = gomokuCandidates();
    if (!candidates.length) return -1;
    // 先走一步随手的棋，月月不再是每一手都算到底。
    if (Math.random() < 0.45) {
      return candidates[Math.floor(Math.random() * candidates.length)];
    }
    var i;
    for (i = 0; i < candidates.length; i++) {
      if (gomokuPotential(candidates[i], 'O') >= 1000000000) return candidates[i];
    }
    for (i = 0; i < candidates.length; i++) {
      if (gomokuPotential(candidates[i], 'X') >= 1000000000) return candidates[i];
    }
    var best = candidates[0];
    var bestScore = -Infinity;
    for (i = 0; i < candidates.length; i++) {
      var index = candidates[i];
      var attack = gomokuPotential(index, 'O');
      var defense = gomokuPotential(index, 'X');
      var x = index % GOMOKU_SIZE;
      var y = Math.floor(index / GOMOKU_SIZE);
      var centerBonus = 7 - (Math.abs(x - 7) + Math.abs(y - 7));
      var score = attack * 1.15 + defense + centerBonus * 4;
      if (score > bestScore) {
        bestScore = score;
        best = index;
      }
    }
    return best;
  }

  function gomokuAiMove() {
    var gomoku = gameState.gomoku;
    if (gomoku.over) return;
    var index = pickGomokuMove();
    if (index < 0) {
      gomoku.busy = false;
      finishGomoku('draw');
      return;
    }
    gomoku.board[index] = 'O';
    renderGomoku();
    if (gomokuWinner(index, 'O')) {
      finishGomoku('lose');
      return;
    }
    if (gomokuBoardFull()) {
      finishGomoku('draw');
      return;
    }
    gomoku.busy = false;
    $('game-gomoku-status').textContent = '轮到你落子。';
  }

  function finishGomoku(result) {
    var gomoku = gameState.gomoku;
    gomoku.over = true;
    gomoku.busy = false;
    stopGomokuTimer();
    var summary;
    var chat;
    if (result === 'win') {
      summary = '你赢了！你先连成了五子。';
      chat = '刚刚跟你下五子棋我赢了，我先连成五子，服不服？';
    } else if (result === 'lose') {
      summary = '月月赢了，她先连成了五子。';
      chat = '刚刚跟你下五子棋我输了，你先连成五子，再来一局？';
    } else {
      summary = '平局，棋盘满了也没人连成五子。';
      chat = '刚刚跟你下五子棋打成平手，棋盘都满了，再来一局？';
    }
    $('game-gomoku-status').textContent = summary;
    showGameResult(summary, chat, {
      name: '五子棋',
      result: result,
      score: ''
    });
  }

  // ---------------------------------------------------------- 四子棋
  function startConnect4() {
    var game = gameState.connect4;
    game.board = [];
    for (var i = 0; i < 42; i++) game.board.push(0);
    game.busy = false;
    game.over = false;
    stopConnect4Timer();
    renderConnect4('你执红，月月执黄，点一列落子。');
  }

  function renderConnect4(message) {
    var board = $('game-connect4-board');
    if (!board) return;
    var game = gameState.connect4;
    board.innerHTML = '';
    for (var i = 0; i < 42; i++) {
      var button = document.createElement('button');
      button.type = 'button';
      button.className = 'game-connect4-cell' +
        (game.board[i] === 1 ? ' player' : game.board[i] === 2 ? ' ai' : '');
      button.setAttribute('data-col', String(i % 7));
      button.setAttribute('aria-label', '第 ' + ((i % 7) + 1) + ' 列');
      button.disabled = Boolean(game.board[i]) || game.busy || game.over;
      board.appendChild(button);
    }
    if (message) $('game-connect4-status').textContent = message;
  }

  function connect4Drop(who, col) {
    var board = gameState.connect4.board;
    for (var row = 5; row >= 0; row--) {
      var index = row * 7 + col;
      if (!board[index]) {
        board[index] = who;
        return row;
      }
    }
    return -1;
  }

  function connect4Winner(who) {
    var board = gameState.connect4.board;
    var directions = [[1, 0], [0, 1], [1, 1], [1, -1]];
    for (var row = 0; row < 6; row++) {
      for (var col = 0; col < 7; col++) {
        if (board[row * 7 + col] !== who) continue;
        for (var d = 0; d < directions.length; d++) {
          var dr = directions[d][0];
          var dc = directions[d][1];
          var count = 1;
          for (var step = 1; step < 4; step++) {
            var r = row + dr * step;
            var c = col + dc * step;
            if (r < 0 || r > 5 || c < 0 || c > 6 || board[r * 7 + c] !== who) break;
            count++;
          }
          if (count >= 4) return true;
        }
      }
    }
    return false;
  }

  function connect4LegalCols() {
    var board = gameState.connect4.board;
    var cols = [];
    for (var col = 0; col < 7; col++) {
      if (!board[col]) cols.push(col);
    }
    return cols;
  }

  function connect4WinningCol(who) {
    var game = gameState.connect4;
    var cols = connect4LegalCols();
    for (var i = 0; i < cols.length; i++) {
      var col = cols[i];
      var row = connect4Drop(who, col);
      if (row >= 0) {
        var win = connect4Winner(who);
        game.board[row * 7 + col] = 0;
        if (win) return col;
      }
    }
    return -1;
  }

  function connect4AiMove() {
    var game = gameState.connect4;
    if (game.over) return;
    var col = -1;
    // 月月会漏看一部分胜点和堵点，玩家更容易连成四子。
    if (Math.random() < 0.5) col = connect4WinningCol(2);
    if (col < 0 && Math.random() < 0.5) col = connect4WinningCol(1);
    if (col < 0) {
      var legal = connect4LegalCols();
      var order = [3, 2, 4, 1, 5, 0, 6];
      if (Math.random() < 0.45) {
        col = legal[Math.floor(Math.random() * legal.length)];
      } else {
        for (var i = 0; i < order.length; i++) {
          if (legal.indexOf(order[i]) >= 0) { col = order[i]; break; }
        }
      }
    }
    if (col == null || col < 0) {
      finishConnect4('draw');
      return;
    }
    connect4Drop(2, col);
    renderConnect4();
    if (connect4Winner(2)) {
      finishConnect4('lose');
      return;
    }
    game.busy = false;
    if (!connect4LegalCols().length) {
      finishConnect4('draw');
      return;
    }
    renderConnect4('轮到你落子。');
  }

  function connect4PlayerMove(col) {
    var game = gameState.connect4;
    if (game.busy || game.over) return;
    if (connect4Drop(1, col) < 0) return;
    renderConnect4();
    if (connect4Winner(1)) {
      finishConnect4('win');
      return;
    }
    if (!connect4LegalCols().length) {
      finishConnect4('draw');
      return;
    }
    game.busy = true;
    renderConnect4('月月在盯着棋盘想……');
    stopConnect4Timer();
    game.timer = window.setTimeout(connect4AiMove, 420);
  }

  function finishConnect4(result) {
    var game = gameState.connect4;
    game.over = true;
    game.busy = false;
    stopConnect4Timer();
    var summary;
    var chat;
    if (result === 'win') {
      summary = '你赢了！先连成了四个。';
      chat = '刚刚四子棋我赢了，先连成四子，服不服？';
    } else if (result === 'lose') {
      summary = '月月赢了，她先连成了四个。';
      chat = '刚刚四子棋我输了，你先连成四子，再来一局？';
    } else {
      summary = '平局，棋盘满了也没人连成四个。';
      chat = '刚刚四子棋打成平手，棋盘都满了，再来一局？';
    }
    renderConnect4(summary);
    showGameResult(summary, chat, { name: '四子棋', result: result, score: '' });
  }

  // ---------------------------------------------------------- 黑白棋
  var REVERSI_DIRECTIONS = [[-1, -1], [-1, 0], [-1, 1], [0, -1], [0, 1], [1, -1], [1, 0], [1, 1]];

  function startReversi() {
    var game = gameState.reversi;
    game.board = [];
    for (var i = 0; i < 64; i++) game.board.push(0);
    game.board[27] = 2;
    game.board[28] = 1;
    game.board[35] = 1;
    game.board[36] = 2;
    game.busy = false;
    game.over = false;
    stopReversiTimer();
    updateReversiScores();
    renderReversi('你执黑先手，点一个能夹住白棋的位置。');
  }

  function reversiFlips(board, index, who) {
    if (index < 0 || index >= 64 || board[index]) return [];
    var row = Math.floor(index / 8);
    var col = index % 8;
    var opponent = who === 1 ? 2 : 1;
    var flips = [];
    REVERSI_DIRECTIONS.forEach(function (dir) {
      var r = row + dir[0];
      var c = col + dir[1];
      var line = [];
      while (r >= 0 && r < 8 && c >= 0 && c < 8 && board[r * 8 + c] === opponent) {
        line.push(r * 8 + c);
        r += dir[0];
        c += dir[1];
      }
      if (line.length && r >= 0 && r < 8 && c >= 0 && c < 8 && board[r * 8 + c] === who) {
        flips = flips.concat(line);
      }
    });
    return flips;
  }

  function reversiMoves(who) {
    var moves = {};
    for (var i = 0; i < 64; i++) {
      var flips = reversiFlips(gameState.reversi.board, i, who);
      if (flips.length) moves[i] = flips;
    }
    return moves;
  }

  function updateReversiScores() {
    var board = gameState.reversi.board;
    var player = 0;
    var ai = 0;
    for (var i = 0; i < 64; i++) {
      if (board[i] === 1) player++;
      else if (board[i] === 2) ai++;
    }
    $('game-reversi-player').textContent = String(player);
    $('game-reversi-ai').textContent = String(ai);
  }

  function renderReversi(message) {
    var node = $('game-reversi-board');
    if (!node) return;
    var game = gameState.reversi;
    var moves = game.busy || game.over ? {} : reversiMoves(1);
    node.innerHTML = '';
    for (var i = 0; i < 64; i++) {
      var button = document.createElement('button');
      button.type = 'button';
      button.className = 'game-reversi-cell' +
        (game.board[i] === 1 ? ' player' : game.board[i] === 2 ? ' ai' : '') +
        (moves[i] ? ' hint' : '');
      button.setAttribute('data-index', String(i));
      button.setAttribute('aria-label', '第 ' + (Math.floor(i / 8) + 1) + ' 行第 ' + (i % 8 + 1) + ' 列');
      button.disabled = !moves[i];
      node.appendChild(button);
    }
    updateReversiScores();
    if (message) $('game-reversi-status').textContent = message;
  }

  function reversiApply(index, who) {
    var board = gameState.reversi.board;
    var flips = reversiFlips(board, index, who);
    if (!flips.length) return false;
    board[index] = who;
    flips.forEach(function (flip) { board[flip] = who; });
    return true;
  }

  function reversiAiMove() {
    var game = gameState.reversi;
    if (game.over) return;
    var moves = reversiMoves(2);
    var keys = Object.keys(moves);
    if (!keys.length) {
      if (!Object.keys(reversiMoves(1)).length) finishReversi();
      else {
        game.busy = false;
        renderReversi('月月没有位置可下，轮到你了。');
      }
      return;
    }
    var best = keys[0];
    if (Math.random() < 0.45) {
      best = keys[Math.floor(Math.random() * keys.length)];
    } else {
      var bestScore = -100;
      keys.forEach(function (key) {
        var index = Number(key);
        var row = Math.floor(index / 8);
        var col = index % 8;
        var corner = (row === 0 || row === 7) && (col === 0 || col === 7);
        var score = moves[key].length + (corner ? 3 : 0) + Math.random();
        if (score > bestScore) { bestScore = score; best = key; }
      });
    }
    reversiApply(Number(best), 2);
    game.busy = false;
    var playerMoves = reversiMoves(1);
    renderReversi(Object.keys(playerMoves).length ? '轮到你落子。' : '你没有位置可下，月月继续。');
    if (!Object.keys(reversiMoves(1)).length && !Object.keys(moves).length) {
      finishReversi();
    } else if (!Object.keys(playerMoves).length) {
      game.busy = true;
      stopReversiTimer();
      game.timer = window.setTimeout(reversiAiMove, 500);
    }
  }

  function reversiPlayerMove(index) {
    var game = gameState.reversi;
    if (game.busy || game.over) return;
    if (!reversiApply(index, 1)) return;
    game.busy = true;
    renderReversi('月月在翻棋……');
    if (!Object.keys(reversiMoves(2)).length) {
      if (!Object.keys(reversiMoves(1)).length) finishReversi();
      else {
        game.busy = false;
        renderReversi('月月没有位置可下，轮到你了。');
      }
      return;
    }
    stopReversiTimer();
    game.timer = window.setTimeout(reversiAiMove, 480);
  }

  function finishReversi() {
    var game = gameState.reversi;
    game.over = true;
    game.busy = false;
    stopReversiTimer();
    var player = 0;
    var ai = 0;
    game.board.forEach(function (value) {
      if (value === 1) player++;
      else if (value === 2) ai++;
    });
    var result = player > ai ? 'win' : player < ai ? 'lose' : 'draw';
    var summary = result === 'win'
      ? '你赢了！黑棋 ' + player + ' 比 ' + ai + '。'
      : result === 'lose'
        ? '月月赢了，白棋 ' + ai + ' 比 ' + player + '。'
        : '平局，黑白棋 ' + player + ' 比 ' + ai + '。';
    renderReversi(summary);
    showGameResult(summary, summary + ' 再来一局？', {
      name: '黑白棋',
      result: result,
      score: player + ':' + ai
    });
  }

