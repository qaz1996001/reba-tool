import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "../style" as Style

Rectangle {
    id: root

    color: Style.Theme.surface
    border.color: Style.Theme.border
    radius: 4
    clip: true

    // scoreTableModel 由 rootContext 提供
    property var model: scoreTableModel

    // 欄位寬度比例
    property var columnRatios: [3, 2, 1, 3, 2]
    property real totalRatio: {
        var sum = 0;
        for (var i = 0; i < columnRatios.length; i++) sum += columnRatios[i];
        return sum;
    }

    function colWidth(index) {
        return (root.width - 4) * columnRatios[index] / totalRatio;
    }

    ListView {
        id: tableView
        anchors.fill: parent
        anchors.margins: 2
        model: root.model
        interactive: false

        delegate: Row {
            id: rowDelegate
            width: tableView.width
            height: Style.Theme.tableRowHeight

            // 從 ListView delegate 取得列索引
            property int rowIndex: index

            Repeater {
                model: 5

                Rectangle {
                    property int ri: rowDelegate.rowIndex

                    width: root.colWidth(index)
                    height: Style.Theme.tableRowHeight
                    color: {
                        var bg = root.model.data(root.model.index(ri, index), 257); // BackgroundColorRole
                        return bg ? bg : "transparent";
                    }

                    Text {
                        anchors.fill: parent
                        anchors.margins: 2
                        text: {
                            var val = root.model.data(root.model.index(parent.ri, index), 0); // DisplayRole
                            return val ? val : "";
                        }
                        font.family: Style.Theme.fontFamily
                        font.pixelSize: {
                            var bold = root.model.data(root.model.index(parent.ri, index), 258); // FontBoldRole
                            return bold ? Style.Theme.formulaTotalFontSize : Style.Theme.formulaDetailFontSize;
                        }
                        font.bold: {
                            var bold = root.model.data(root.model.index(parent.ri, index), 258);
                            return bold ? true : false;
                        }
                        color: Style.Theme.text
                        horizontalAlignment: {
                            var align = root.model.data(root.model.index(parent.ri, index), 260); // TextAlignRole
                            if (align === "right") return Text.AlignRight;
                            return Text.AlignHCenter;
                        }
                        verticalAlignment: Text.AlignVCenter
                        elide: Text.ElideRight
                    }
                }
            }
        }
    }
}
