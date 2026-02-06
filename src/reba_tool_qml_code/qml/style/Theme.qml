pragma Singleton
import QtQuick 2.15

/**
 * 深色霓虹主題 Singleton
 * 所有顏色、字體、布局常數皆由此統一管理
 */
QtObject {
    // ── 背景色 ──
    readonly property color bgDeepNavy:   "#0a0f1d"
    readonly property color bgCharcoal:   "#161c2d"
    readonly property color cardBg:       "#1e2539"

    // ── 強調色 ──
    readonly property color accentNeonBlue:  "#00f2ff"
    readonly property color accentNeonGreen: "#39ff14"

    // ── 邊框 ──
    readonly property color borderNavy: "#2d3748"

    // ── 文字 ──
    readonly property color textPrimary:   "#f8fafc"
    readonly property color textSecondary: "#94a3b8"
    readonly property color textMuted:     "#64748b"

    // ── 表面色 ──
    readonly property color surface800: "#1e293b"
    readonly property color surface900: "#0f172a"

    // ── 風險等級色 ──
    readonly property color riskNegligible: "#10b981"
    readonly property color riskLow:        "#10b981"
    readonly property color riskMedium:     "#fbbf24"
    readonly property color riskHigh:       "#f43f5e"
    readonly property color riskVeryHigh:   "#dc2626"

    // ── 字體 ──
    readonly property string fontFamily:    "Segoe UI"
    readonly property string fontFamilyCjk: "Microsoft YaHei"
    readonly property int fontXs:   9
    readonly property int fontSm:   11
    readonly property int fontMd:   13
    readonly property int fontLg:   16
    readonly property int fontXl:   20
    readonly property int fontXxl:  28
    readonly property int fontHuge: 42

    // ── 布局 ──
    readonly property int headerHeight:     48
    readonly property int footerHeight:     24
    readonly property int sidePanelWidth:   320
    readonly property int sidePanelMinWidth:300
    readonly property int bottomHeight:     260
    readonly property int spacing:          0
    readonly property int padding:          16
    readonly property int borderRadius:     8
    readonly property int borderWidth:      1

    // ── 比例 ──
    readonly property real bottomLeftRatio:  0.25
    readonly property real bottomRightRatio: 0.35

    /**
     * 根據風險等級回傳對應顏色
     */
    function riskColor(level) {
        if (level <= 1) return riskNegligible
        if (level <= 3) return riskLow
        if (level <= 7) return riskMedium
        if (level <= 10) return riskHigh
        return riskVeryHigh
    }

    /**
     * 從 JSON 配置覆蓋主題（預留，Phase 2 用）
     */
    function loadTheme(cfg) {
        // 未來可動態覆蓋屬性
    }
}
