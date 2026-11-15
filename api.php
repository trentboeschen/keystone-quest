<?php
// Keystone Quest API
//   GET  api.php?action=list     every adventure in adventures/*.json (drafts only for editors)
//   GET  api.php?action=auth     checks the editor password (X-Edit-Key header)
//   POST api.php?action=save     body {adventure, base, isNew}; writes adventures/<id>.json
//   POST api.php?action=delete   body {id}; moves the file into adventures/_backups/
// Each adventure file holds its listing info (title, era, blurb, art, accent),
// a "published" true/false, an "updated" timestamp, the start scene and the scenes.

require __DIR__ . '/config.php';

header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: no-store');

const ADV_DIR = __DIR__ . '/adventures';
const BACKUP_DIR = ADV_DIR . '/_backups';
const MAX_BYTES = 1048576;

function out(int $code, $data): void {
    http_response_code($code);
    echo json_encode($data, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
    exit;
}

function is_editor(): bool {
    $key = $_SERVER['HTTP_X_EDIT_KEY'] ?? '';
    return EDIT_PASSWORD !== '' && $key !== '' && hash_equals(EDIT_PASSWORD, $key);
}

function require_editor(): void {
    if (!is_editor()) {
        usleep(400000); // slows down password guessing
        out(401, ['error' => 'Editor password needed.']);
    }
}

function valid_id($id): bool {
    return is_string($id) && preg_match('/^[a-z0-9][a-z0-9-]{0,63}$/', $id) === 1;
}

// Returns an error message, or null when the adventure is usable.
function check_adventure($a): ?string {
    if (!is_object($a)) return 'Adventure must be an object.';
    if (!isset($a->title) || !is_string($a->title) || trim($a->title) === '') return 'Adventure needs a title.';
    if (!isset($a->scenes) || !is_object($a->scenes) || count(get_object_vars($a->scenes)) === 0) return 'Adventure needs at least one scene.';
    if (!isset($a->start) || !is_string($a->start) || !property_exists($a->scenes, $a->start)) return 'The starting scene does not exist.';
    foreach (get_object_vars($a->scenes) as $sid => $s) {
        if (!is_object($s)) return "Scene \"$sid\" is not valid.";
        if (isset($s->choices) && !is_array($s->choices)) return "Scene \"$sid\" has invalid choices.";
    }
    return null;
}

function read_adventure(string $file) {
    $raw = @file_get_contents($file);
    if ($raw === false) return null;
    $a = json_decode($raw);
    if (check_adventure($a) !== null) return null;
    $a->id = basename($file, '.json'); // the file name is the id
    $a->published = !empty($a->published);
    // "updated" is the version used to catch two people saving over each other.
    // If the file was edited by hand after its last save, the file's time wins so the editor notices.
    $mtime = (int)(filemtime($file) * 1000);
    $a->updated = isset($a->updated) ? (int)$a->updated : 0;
    if ($mtime > $a->updated + 2000) $a->updated = $mtime;
    return $a;
}

function backup(string $id): void {
    $src = ADV_DIR . "/$id.json";
    if (!is_file($src)) return;
    if (!is_dir(BACKUP_DIR)) @mkdir(BACKUP_DIR, 0775, true);
    @copy($src, BACKUP_DIR . "/$id." . gmdate('Ymd-His') . '-' . substr(uniqid(), -4) . '.json');
    $old = glob(BACKUP_DIR . "/$id.*.json") ?: [];
    sort($old);
    while (count($old) > BACKUPS_PER_ADVENTURE) @unlink(array_shift($old));
}

function body() {
    $raw = file_get_contents('php://input', false, null, 0, MAX_BYTES + 1);
    if ($raw === false || strlen($raw) > MAX_BYTES) out(413, ['error' => 'That adventure is too large.']);
    $b = json_decode($raw);
    if (!is_object($b)) out(400, ['error' => 'Request was not valid JSON.']);
    return $b;
}

$action = $_GET['action'] ?? '';
$method = $_SERVER['REQUEST_METHOD'];

if ($action === 'list' && $method === 'GET') {
    $editor = is_editor();
    $list = [];
    foreach (glob(ADV_DIR . '/*.json') ?: [] as $file) {
        $a = read_adventure($file);
        if ($a && ($a->published || $editor)) $list[] = $a;
    }
    usort($list, fn($x, $y) => strcasecmp($x->title, $y->title));
    out(200, ['adventures' => $list, 'editor' => $editor, 'editing' => EDIT_PASSWORD !== '']);
}

if ($action === 'auth' && $method === 'GET') {
    require_editor();
    out(200, ['ok' => true]);
}

if ($action === 'save' && $method === 'POST') {
    require_editor();
    $b = body();
    $a = $b->adventure ?? null;
    $err = check_adventure($a);
    if ($err) out(422, ['error' => $err]);
    $id = $a->id ?? '';
    if (!valid_id($id)) out(422, ['error' => 'File name must use lowercase letters, numbers and dashes.']);
    $file = ADV_DIR . "/$id.json";
    if (!is_dir(ADV_DIR) || !is_writable(ADV_DIR)) out(500, ['error' => 'The server cannot write to the adventures folder. Check its permissions.']);

    $fp = fopen(ADV_DIR . '/.lock', 'c');
    flock($fp, LOCK_EX);
    $current = is_file($file) ? read_adventure($file) : null;
    if (!empty($b->isNew) && is_file($file)) {
        flock($fp, LOCK_UN);
        out(409, ['error' => "An adventure with the file name \"$id\" already exists. Choose another file name."]);
    }
    if (empty($b->isNew) && $current && isset($b->base) && (int)$b->base !== $current->updated) {
        flock($fp, LOCK_UN);
        out(409, ['error' => 'Someone saved this adventure after you opened it.', 'updated' => $current->updated, 'conflict' => true]);
    }
    backup($id);
    $a->published = !empty($a->published);
    $a->updated = (int)round(microtime(true) * 1000);
    unset($a->builtin);
    $ordered = (object)array_merge(
        ['id' => $id, 'title' => '', 'era' => '', 'blurb' => '', 'art' => 'none', 'accent' => '#5a6fb0', 'published' => false, 'updated' => 0, 'start' => ''],
        get_object_vars($a)
    );
    $json = json_encode($ordered, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES) . "\n";
    $tmp = $file . '.tmp';
    $ok = file_put_contents($tmp, $json) !== false && rename($tmp, $file);
    flock($fp, LOCK_UN);
    if (!$ok) out(500, ['error' => 'Saving failed on the server.']);
    out(200, ['ok' => true, 'id' => $id, 'updated' => $a->updated]);
}

if ($action === 'delete' && $method === 'POST') {
    require_editor();
    $b = body();
    $id = $b->id ?? '';
    if (!valid_id($id) || !is_file(ADV_DIR . "/$id.json")) out(404, ['error' => 'Adventure not found.']);
    backup($id);
    @unlink(ADV_DIR . "/$id.json");
    out(200, ['ok' => true]);
}

out(404, ['error' => 'Unknown request.']);
