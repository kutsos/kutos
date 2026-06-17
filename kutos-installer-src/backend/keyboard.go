package backend

import (
	"bufio"
	"os"
	"sort"
	"strings"
)

// KeyboardLayout bir XKB klavye düzenini temsil eder.
type KeyboardLayout struct {
	Code        string
	Description string
}

// ListKeyboardLayouts XKB evdev listesinden mevcut klavye düzenlerini döndürür.
func ListKeyboardLayouts() []KeyboardLayout {
	f, err := os.Open("/usr/share/X11/xkb/rules/evdev.lst")
	if err != nil {
		return []KeyboardLayout{
			{Code: "tr", Description: "Turkish"},
			{Code: "us", Description: "English (US)"},
			{Code: "de", Description: "German"},
		}
	}
	defer f.Close()

	var layouts []KeyboardLayout
	inLayouts := false

	scanner := bufio.NewScanner(f)
	for scanner.Scan() {
		line := scanner.Text()
		if strings.HasPrefix(line, "! layout") {
			inLayouts = true
			continue
		}
		if inLayouts && strings.HasPrefix(line, "!") {
			break
		}
		if inLayouts {
			trimmed := strings.TrimSpace(line)
			if trimmed == "" {
				continue
			}
			parts := strings.SplitN(trimmed, " ", 2)
			if len(parts) == 2 {
				layouts = append(layouts, KeyboardLayout{
					Code:        strings.TrimSpace(parts[0]),
					Description: strings.TrimSpace(parts[1]),
				})
			}
		}
	}

	sort.Slice(layouts, func(i, j int) bool {
		return layouts[i].Description < layouts[j].Description
	})
	return layouts
}
