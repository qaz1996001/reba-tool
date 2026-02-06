import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "../style" as Style

/**
 * 底部右側：Table C 12×12 矩陣
 * 顯示 Score A (row) × Score B (col) 的對照表
 * 高亮目前的交叉格
 */
Rectangle {
    id: root
    color: Style.Theme.bgCharcoal

    // ── 佔位資料（Phase 2 由 TableCModel 綁定）──
    property int scoreA: 4
    property int scoreB: 5

    // Table C 查找表（12×12）
    property var tableCData: [
        [1,1,1,2,3,3,4,5,6,7,7,7],
        [1,2,2,3,4,4,5,6,6,7,7,8],
        [2,3,3,3,4,5,6,7,7,8,8,8],
        [3,4,4,4,5,6,6,7,8,8,9,9],
        [4,4,4,5,6,7,8,8,9,9,10,10],
        [5,5,6,7,8,8,9,9,10,10,11,11],
        [6,6,7,8,8,9,9,10,10,11,11,12],
        [7,7,8,9,9,10,10,11,11,12,12,12],
        [8,8,9,10,10,10,11,11,12,12,12,12],
        [9,9,10,10,10,11,11,12,12,12,12,12],
        [10,10,10,11,11,12,12,12,12,12,12,12],
        [11,11,11,12,12,12,12,12,12,12,12,12]
    ]

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: Style.Theme.padding
        spacing: 10

        // 標題
        Row {
            spacing: 8
            Text {
                text: "\u25A6"  // ▦
                font.pixelSize: Style.Theme.fontSm
                color: Style.Theme.textMuted
            }
            Text {
                text: "TABLE C 矩陣"
                font.pixelSize: Style.Theme.fontSm
                font.bold: true
                font.letterSpacing: 3
                font.capitalization: Font.AllUppercase
                color: Style.Theme.textMuted
                anchors.verticalCenter: parent.verticalCenter
            }
        }

        // 12×12 矩陣
        Grid {
            id: matrixGrid
            Layout.fillWidth: true
            Layout.fillHeight: true
            columns: 12
            spacing: 1

            Repeater {
                model: 144  // 12 × 12

                Rectangle {
                    id: cell
                    property int row: Math.floor(index / 12)
                    property int col: index % 12
                    property int cellValue: root.tableCData[row][col]
                    property bool isActive: (row === root.scoreA - 1) && (col === root.scoreB - 1)
                    property bool isRowHighlight: row === root.scoreA - 1
                    property bool isColHighlight: col === root.scoreB - 1

                    width: (matrixGrid.width - 11) / 12
                    height: (matrixGrid.height - 11) / 12

                    radius: isActive ? 3 : 0
                    color: {
                        if (isActive) return Style.Theme.accentNeonBlue
                        if (isRowHighlight || isColHighlight)
                            return Qt.rgba(Style.Theme.accentNeonBlue.r,
                                           Style.Theme.accentNeonBlue.g,
                                           Style.Theme.accentNeonBlue.b, 0.12)
                        return Qt.rgba(Style.Theme.surface900.r,
                                       Style.Theme.surface900.g,
                                       Style.Theme.surface900.b, 0.8)
                    }
                    border.color: Qt.rgba(255, 255, 255, 0.03)
                    border.width: 1

                    Text {
                        anchors.centerIn: parent
                        text: cell.cellValue
                        font.pixelSize: Math.max(8, Math.min(11, cell.width * 0.4))
                        font.family: "Consolas"
                        font.weight: cell.isActive ? Font.Black : Font.Normal
                        color: {
                            if (cell.isActive) return Style.Theme.surface900
                            if (cell.isRowHighlight || cell.isColHighlight)
                                return Style.Theme.accentNeonBlue
                            return Style.Theme.textMuted
                        }
                    }
                }
            }
        }

        // 底部資訊
        RowLayout {
            Layout.fillWidth: true
            Text {
                text: "Row: A (" + root.scoreA + ") | Col: B (" + root.scoreB + ")"
                font.pixelSize: Style.Theme.fontXs
                font.family: "Consolas"
                color: Style.Theme.textMuted
            }
            Item { Layout.fillWidth: true }
            Row {
                spacing: 6
                Text {
                    text: "FINAL:"
                    font.pixelSize: Style.Theme.fontXs
                    font.bold: true
                    font.capitalization: Font.AllUppercase
                    color: Style.Theme.textMuted
                }
                Text {
                    text: {
                        var a = root.scoreA - 1
                        var b = root.scoreB - 1
                        if (a >= 0 && a < 12 && b >= 0 && b < 12)
                            return root.tableCData[a][b].toString().padStart(2, '0')
                        return "--"
                    }
                    font.pixelSize: Style.Theme.fontMd
                    font.weight: Font.Black
                    color: Style.Theme.accentNeonBlue
                }
            }
        }
    }
}
