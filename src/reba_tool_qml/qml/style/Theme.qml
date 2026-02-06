pragma Singleton
import QtQuick 2.15

QtObject {
    id: theme

    // ========== 視窗 ==========
    property int windowX: 100
    property int windowY: 100
    property int windowWidth: 1400
    property int windowHeight: 900

    // ========== 顏色 ==========
    property color background: "#0a0f1d"
    property color surface: "#1e2539"
    property color surfaceAlt: "#161c2d"
    property color border: "#2d3748"
    property color text: "#e2e8f0"
    property color textSecondary: "#94a3b8"
    property color accent: "#00f2ff"
    property color accentLight: "#0a3d42"
    property color headerBg: "#1a2235"
    property color sectionBg: "#151b2c"
    property color sectionSplitBg: "#1a2235"
    property color highlightRow: "#0a2a3a"
    property color totalRow: "#2a1525"
    property color videoBackground: "#060b16"
    property color videoBorder: "#00f2ff"
    property color buttonBg: "#1e2539"
    property color buttonHover: "#283350"
    property color buttonPressed: "#0d4f54"
    property color buttonText: "#00f2ff"
    property color logBackground: "#0d1117"
    property color logText: "#39ff14"

    // ========== 風險顏色 ==========
    property color riskNegligible: "#10b981"
    property color riskLow: "#34d399"
    property color riskMedium: "#fbbf24"
    property color riskHigh: "#f43f5e"
    property color riskVeryHigh: "#ff0000"
    property color riskUnknown: "#475569"

    // ========== 字體 ==========
    property string fontFamily: "Microsoft YaHei"
    property int buttonFontSize: 18
    property int groupboxFontSize: 18
    property int comboboxFontSize: 16
    property int checkboxFontSize: 16
    property int paramLabelFontSize: 16
    property int angleLabelFontSize: 24
    property int rebaScoreFontSize: 28
    property int riskLevelFontSize: 24
    property int riskDescFontSize: 12
    property int formulaHeaderFontSize: 14
    property int formulaDetailFontSize: 11
    property int formulaTotalFontSize: 18
    property int statsFontSize: 24
    property int timeLabelFontSize: 12
    property int videoHintFontSize: 16
    property int logTextFontSize: 10

    // ========== 影片 ==========
    property int videoMinWidth: 600
    property int videoMinHeight: 450
    property int videoBorderWidth: 2

    // ========== 表格 ==========
    property int tableRowHeight: 28
    property int tableHeaderHeight: 32

    // ========== 佈局 ==========
    property int leftRatio: 16
    property int rightRatio: 9
    property int spacing: 8
    property int margin: 8
    property int logMaxHeight: 150
    property int sliderThrottleMs: 150

    // ========== 主題名稱 ==========
    property string themeName: "霓虹深海主題"

    // ========== 風險顏色查詢 ==========
    function riskColor(level) {
        switch (level) {
            case "negligible": return riskNegligible;
            case "low": return riskLow;
            case "medium": return riskMedium;
            case "high": return riskHigh;
            case "very_high": return riskVeryHigh;
            default: return riskUnknown;
        }
    }

    // ========== 載入主題 ==========
    function loadTheme(jsonObj) {
        if (!jsonObj) return;

        themeName = jsonObj.name || themeName;

        // 視窗
        if (jsonObj.window) {
            windowX = jsonObj.window.x || windowX;
            windowY = jsonObj.window.y || windowY;
            windowWidth = jsonObj.window.width || windowWidth;
            windowHeight = jsonObj.window.height || windowHeight;
        }

        // 顏色
        if (jsonObj.colors) {
            var c = jsonObj.colors;
            background = c.background || background;
            surface = c.surface || surface;
            surfaceAlt = c.surfaceAlt || surfaceAlt;
            border = c.border || border;
            text = c.text || text;
            textSecondary = c.textSecondary || textSecondary;
            accent = c.accent || accent;
            accentLight = c.accentLight || accentLight;
            headerBg = c.headerBg || headerBg;
            sectionBg = c.sectionBg || sectionBg;
            sectionSplitBg = c.sectionSplitBg || sectionSplitBg;
            highlightRow = c.highlightRow || highlightRow;
            totalRow = c.totalRow || totalRow;
            videoBackground = c.videoBackground || videoBackground;
            videoBorder = c.videoBorder || videoBorder;
            buttonBg = c.buttonBg || buttonBg;
            buttonHover = c.buttonHover || buttonHover;
            buttonPressed = c.buttonPressed || buttonPressed;
            buttonText = c.buttonText || buttonText;
            logBackground = c.logBackground || logBackground;
            logText = c.logText || logText;
        }

        // 風險顏色
        if (jsonObj.risk_colors) {
            var rc = jsonObj.risk_colors;
            riskNegligible = rc.negligible || riskNegligible;
            riskLow = rc.low || riskLow;
            riskMedium = rc.medium || riskMedium;
            riskHigh = rc.high || riskHigh;
            riskVeryHigh = rc.very_high || riskVeryHigh;
            riskUnknown = rc.unknown || riskUnknown;
        }

        // 字體
        if (jsonObj.fonts) {
            var f = jsonObj.fonts;
            fontFamily = f.family || fontFamily;
            buttonFontSize = f.button_size || buttonFontSize;
            groupboxFontSize = f.groupbox_size || groupboxFontSize;
            comboboxFontSize = f.combobox_size || comboboxFontSize;
            checkboxFontSize = f.checkbox_size || checkboxFontSize;
            paramLabelFontSize = f.param_label_size || paramLabelFontSize;
            angleLabelFontSize = f.angle_label_size || angleLabelFontSize;
            rebaScoreFontSize = f.reba_score_size || rebaScoreFontSize;
            riskLevelFontSize = f.risk_level_size || riskLevelFontSize;
            riskDescFontSize = f.risk_desc_size || riskDescFontSize;
            formulaHeaderFontSize = f.formula_header_size || formulaHeaderFontSize;
            formulaDetailFontSize = f.formula_detail_size || formulaDetailFontSize;
            formulaTotalFontSize = f.formula_total_size || formulaTotalFontSize;
            statsFontSize = f.stats_size || statsFontSize;
            timeLabelFontSize = f.time_label_size || timeLabelFontSize;
            videoHintFontSize = f.video_hint_size || videoHintFontSize;
            logTextFontSize = f.log_text_size || logTextFontSize;
        }

        // 影片
        if (jsonObj.video) {
            videoMinWidth = jsonObj.video.min_width || videoMinWidth;
            videoMinHeight = jsonObj.video.min_height || videoMinHeight;
            videoBorderWidth = jsonObj.video.border_width || videoBorderWidth;
        }

        // 表格
        if (jsonObj.table) {
            tableRowHeight = jsonObj.table.row_height || tableRowHeight;
            tableHeaderHeight = jsonObj.table.header_height || tableHeaderHeight;
        }

        // 佈局
        if (jsonObj.layout) {
            var l = jsonObj.layout;
            leftRatio = l.left_ratio || leftRatio;
            rightRatio = l.right_ratio || rightRatio;
            spacing = l.spacing || spacing;
            margin = l.margin || margin;
            logMaxHeight = l.log_max_height || logMaxHeight;
            sliderThrottleMs = l.slider_throttle_ms || sliderThrottleMs;
        }
    }
}
