/* KutOS Installer Slideshow */
import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Presentation {
    id: presentation

    Timer {
        interval: 5000
        running: true
        repeat: true
        onTriggered: presentation.goToNextSlide()
    }

    Slide {
        Rectangle {
            anchors.fill: parent
            color: "#09090b"

            ColumnLayout {
                anchors.centerIn: parent
                spacing: 20

                Text {
                    text: "Welcome to KutOS"
                    font.pixelSize: 32
                    font.weight: Font.Bold
                    color: "#fafafa"
                    Layout.alignment: Qt.AlignHCenter
                }

                Text {
                    text: "A modern Arch-based Linux distribution\ndesigned for speed, simplicity, and customization."
                    font.pixelSize: 16
                    color: "#a1a1aa"
                    horizontalAlignment: Text.AlignHCenter
                    Layout.alignment: Qt.AlignHCenter
                }
            }
        }
    }

    Slide {
        Rectangle {
            anchors.fill: parent
            color: "#09090b"

            ColumnLayout {
                anchors.centerIn: parent
                spacing: 20

                Text {
                    text: "🚀 Blazing Fast"
                    font.pixelSize: 28
                    font.weight: Font.Bold
                    color: "#fafafa"
                    Layout.alignment: Qt.AlignHCenter
                }

                Text {
                    text: "Built on Arch Linux for maximum performance.\nOnly the packages you need, nothing more."
                    font.pixelSize: 15
                    color: "#a1a1aa"
                    horizontalAlignment: Text.AlignHCenter
                    Layout.alignment: Qt.AlignHCenter
                }
            }
        }
    }

    Slide {
        Rectangle {
            anchors.fill: parent
            color: "#09090b"

            ColumnLayout {
                anchors.centerIn: parent
                spacing: 20

                Text {
                    text: "🎨 Fully Customizable"
                    font.pixelSize: 28
                    font.weight: Font.Bold
                    color: "#fafafa"
                    Layout.alignment: Qt.AlignHCenter
                }

                Text {
                    text: "Choose your desktop environment.\nMake KutOS truly yours with KutOS Settings."
                    font.pixelSize: 15
                    color: "#a1a1aa"
                    horizontalAlignment: Text.AlignHCenter
                    Layout.alignment: Qt.AlignHCenter
                }
            }
        }
    }

    Slide {
        Rectangle {
            anchors.fill: parent
            color: "#09090b"

            ColumnLayout {
                anchors.centerIn: parent
                spacing: 20

                Text {
                    text: "✨ Almost There"
                    font.pixelSize: 28
                    font.weight: Font.Bold
                    color: "#fafafa"
                    Layout.alignment: Qt.AlignHCenter
                }

                Text {
                    text: "Your system is being installed.\nSit back and relax while we set things up."
                    font.pixelSize: 15
                    color: "#a1a1aa"
                    horizontalAlignment: Text.AlignHCenter
                    Layout.alignment: Qt.AlignHCenter
                }
            }
        }
    }
}
