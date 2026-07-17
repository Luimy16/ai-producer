<?php
/**
 * Plugin Name:       VideoClip Creator IA
 * Description:       Crea videoclips con IA en 5 pasos: sube tu canción, elige concepto, diseña personajes, storyboard automático y genera/ensambla. Conecta con el backend "Orquestador" (FastAPI). Shortcode: [videoclip_creator]
 * Version:           1.0.0
 * Author:            Tú
 * License:           GPL-2.0+
 * Text Domain:       vcc
 */

if (!defined('ABSPATH')) { exit; }

final class VCC_Plugin {

    public static function init(): void {
        add_shortcode('videoclip_creator', [__CLASS__, 'shortcode']);
        add_action('wp_enqueue_scripts', [__CLASS__, 'assets']);
        add_action('admin_menu',        [__CLASS__, 'admin_menu']);
        add_action('admin_init',        [__CLASS__, 'admin_settings']);
        add_action('rest_api_init',     [__CLASS__, 'rest_routes']);
    }

    /* ================= Ajustes (wp-admin) ================= */

    public static function admin_menu(): void {
        add_options_page('VideoClip Creator', 'VideoClip Creator', 'manage_options', 'vcc', [__CLASS__, 'admin_page']);
    }

    public static function admin_settings(): void {
        register_setting('vcc', 'vcc_backend_url',   ['default' => 'http://127.0.0.1:8000', 'sanitize_callback' => 'esc_url_raw']);
        register_setting('vcc', 'vcc_backend_token', ['default' => '', 'sanitize_callback' => 'sanitize_text_field']);
    }

    public static function admin_page(): void { ?>
        <div class="wrap">
            <h1>🎬 VideoClip Creator IA</h1>
            <p>Conexión con el backend Orquestador (FastAPI). Usa el shortcode <code>[videoclip_creator]</code> en cualquier página.</p>
            <form method="post" action="options.php">
                <?php settings_fields('vcc'); ?>
                <table class="form-table">
                    <tr>
                        <th><label for="vcc_backend_url">URL del Orquestador</label></th>
                        <td><input type="url" id="vcc_backend_url" name="vcc_backend_url" class="regular-text"
                               value="<?php echo esc_attr(get_option('vcc_backend_url', 'http://127.0.0.1:8000')); ?>" />
                            <p class="description">Ej: http://127.0.0.1:8000 (si está en el mismo VPS)</p></td>
                    </tr>
                    <tr>
                        <th><label for="vcc_backend_token">Token compartido (VCC_TOKEN)</label></th>
                        <td><input type="text" id="vcc_backend_token" name="vcc_backend_token" class="regular-text"
                               value="<?php echo esc_attr(get_option('vcc_backend_token', '')); ?>" />
                            <p class="description">Debe coincidir con VCC_TOKEN del archivo .env del orquestador.</p></td>
                    </tr>
                </table>
                <?php submit_button(); ?>
            </form>
        </div>
    <?php }

    /* ================= Assets (solo donde hay shortcode) ================= */

    public static function assets(): void {
        global $post;
        if (!is_a($post, 'WP_Post') || !has_shortcode($post->post_content, 'videoclip_creator')) { return; }
        wp_enqueue_style('vcc', plugin_dir_url(__FILE__) . 'assets/wizard.css', [], '1.0.0');
        wp_enqueue_script('vcc', plugin_dir_url(__FILE__) . 'assets/wizard.js', [], '1.0.0', true);
        wp_localize_script('vcc', 'VCC', [
            'rest'  => esc_url_raw(rest_url('vcc/v1/')),
            'nonce' => wp_create_nonce('wp_rest'),
        ]);
    }

    /* ================= Shortcode: el wizard ================= */

    public static function shortcode(): string {
        if (!is_user_logged_in()) {
            return '<div class="vcc-login-aviso">🔒 Debes <a href="' . esc_url(wp_login_url(get_permalink())) . '">iniciar sesión</a> para crear tu videoclip.</div>';
        }
        ob_start(); ?>
        <div id="vcc-app" class="vcc-app">

            <ol class="vcc-pasos">
                <li data-paso="1" class="activo">🎵 Canción</li>
                <li data-paso="2">🎨 Concepto</li>
                <li data-paso="3">🎭 Personaje</li>
                <li data-paso="4">🎞 Storyboard</li>
                <li data-paso="5">🚀 Videoclip</li>
            </ol>

            <!-- PASO 1: subir canción -->
            <section class="vcc-step activo" data-step="1">
                <h2>🎵 Sube tu canción</h2>
                <p class="vcc-muted">La IA analizará el BPM, el ritmo y la estructura para sincronizar cada escena.</p>
                <label class="vcc-label">Archivo de audio (mp3/wav):</label>
                <input type="file" id="vcc-audio" accept="audio/*" />
                <label class="vcc-label">Letra de la canción:</label>
                <textarea id="vcc-letra" rows="8" placeholder="Pega aquí la letra..."></textarea>
                <label class="vcc-label">Formato:</label>
                <select id="vcc-formato">
                    <option value="16:9">Horizontal 16:9 (YouTube)</option>
                    <option value="9:16">Vertical 9:16 (Reels / TikTok)</option>
                </select>
                <button class="vcc-btn" id="vcc-subir" disabled>Analizar canción →</button>
                <div class="vcc-analisis" id="vcc-analisis" hidden></div>
            </section>

            <!-- PASO 2: conceptos -->
            <section class="vcc-step" data-step="2">
                <h2>🎨 Elige el concepto visual</h2>
                <p class="vcc-muted">La IA propone 3 direcciones de arte distintas. Tú decides.</p>
                <button class="vcc-btn" id="vcc-gen-conceptos">Generar 3 conceptos ✨</button>
                <div class="vcc-cards" id="vcc-conceptos"></div>
            </section>

            <!-- PASO 3: personaje -->
            <section class="vcc-step" data-step="3">
                <h2>🎭 Diseña tu personaje</h2>
                <p class="vcc-muted">La IA crea una hoja de personaje coherente con el concepto elegido.</p>
                <label class="vcc-label">Descripción del personaje (edítala a tu gusto):</label>
                <textarea id="vcc-personaje-desc" rows="3"></textarea>
                <button class="vcc-btn" id="vcc-gen-personaje">Generar hoja de personaje 🖼</button>
                <div class="vcc-personaje" id="vcc-personaje-out"></div>
                <button class="vcc-btn vcc-btn-ok" id="vcc-aprobar-personaje" hidden>Aprobar personaje →</button>
            </section>

            <!-- PASO 4: storyboard -->
            <section class="vcc-step" data-step="4">
                <h2>🎞 Storyboard automático</h2>
                <p class="vcc-muted">Cada escena tiene duración exacta sincronizada con el beat. Edita los prompts si quieres.</p>
                <button class="vcc-btn" id="vcc-gen-storyboard">Crear storyboard 🧠</button>
                <div id="vcc-storyboard"></div>
                <button class="vcc-btn vcc-btn-ok" id="vcc-generar-todo" hidden>🎬 Generar todas las escenas</button>
                <div class="vcc-progreso" id="vcc-progreso" hidden>
                    <div class="vcc-barra"><div class="vcc-barra-fill" id="vcc-barra-fill"></div></div>
                    <p id="vcc-progreso-txt">Generando...</p>
                </div>
            </section>

            <!-- PASO 5: ensamblar -->
            <section class="vcc-step" data-step="5">
                <h2>🚀 Tu videoclip</h2>
                <button class="vcc-btn" id="vcc-ensamblar">Ensamblar videoclip final 🎬</button>
                <div id="vcc-final"></div>
            </section>

            <div class="vcc-error" id="vcc-error" hidden></div>
        </div>
        <?php
        return (string) ob_get_clean();
    }

    /* ================= REST API (proxy seguro al orquestador) ================= */

    public static function rest_routes(): void {
        register_rest_route('vcc/v1', '/proxy', [
            'methods'             => 'POST',
            'callback'            => [__CLASS__, 'proxy'],
            'permission_callback' => function () { return is_user_logged_in(); },
        ]);
        register_rest_route('vcc/v1', '/subir-audio', [
            'methods'             => 'POST',
            'callback'            => [__CLASS__, 'subir_audio'],
            'permission_callback' => function () { return is_user_logged_in(); },
        ]);
    }

    private static function backend(string $path): string {
        return rtrim(get_option('vcc_backend_url', 'http://127.0.0.1:8000'), '/') . '/api/' . ltrim($path, '/');
    }

    public static function proxy(WP_REST_Request $req) {
        $ruta   = (string) $req->get_param('ruta');
        $metodo = strtoupper((string) ($req->get_param('metodo') ?: 'POST'));
        // Whitelist: solo rutas del tipo "proyecto", "proyecto/xxx/conceptos", etc.
        if (!preg_match('#^(proyecto(/[a-zA-Z0-9_-]+)?(/(conceptos|personaje|storyboard|escenas/[0-9]+/(imagen|video|lipsync)|ensamblar|archivo/[a-zA-Z0-9_.-]+))?|workers/estado)$#', $ruta)) {
            return new WP_Error('vcc_bad_route', 'Ruta no permitida', ['status' => 400]);
        }
        $args = [
            'timeout' => 600,
            'headers' => ['X-Token' => get_option('vcc_backend_token', '')],
        ];
        if ($metodo === 'GET') {
            $res = wp_remote_get(self::backend($ruta), $args);
        } else {
            $args['headers']['Content-Type'] = 'application/json';
            $args['body'] = wp_json_encode($req->get_param('datos') ?: new stdClass());
            $res = wp_remote_post(self::backend($ruta), $args);
        }
        if (is_wp_error($res)) { return $res; }
        $code = wp_remote_retrieve_response_code($res);
        $body = wp_remote_retrieve_body($res);
        $json = json_decode($body, true);
        return new WP_REST_Response($json !== null ? $json : ['raw' => $body], $code ?: 500);
    }

    public static function subir_audio(WP_REST_Request $req) {
        $files = $req->get_file_params();
        if (empty($files['audio']['tmp_name'])) {
            return new WP_Error('vcc_no_audio', 'Falta el archivo de audio', ['status' => 400]);
        }
        $ch = curl_init(self::backend('proyecto'));
        curl_setopt_array($ch, [
            CURLOPT_POST           => true,
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_TIMEOUT        => 300,
            CURLOPT_HTTPHEADER     => ['X-Token: ' . get_option('vcc_backend_token', '')],
            CURLOPT_POSTFIELDS     => [
                'audio'   => new CURLFile($files['audio']['tmp_name'], $files['audio']['type'] ?: 'audio/mpeg', $files['audio']['name']),
                'letra'   => (string) $req->get_param('letra'),
                'formato' => (string) ($req->get_param('formato') ?: '16:9'),
            ],
        ]);
        $body = curl_exec($ch);
        $code = (int) curl_getinfo($ch, CURLINFO_RESPONSE_CODE);
        curl_close($ch);
        $json = json_decode((string) $body, true);
        return new WP_REST_Response($json !== null ? $json : ['error' => (string) $body], $code ?: 500);
    }
}

VCC_Plugin::init();
