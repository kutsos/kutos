package backend

import (
	"os"
	"path/filepath"
	"sort"
	"strings"
)

// ListTimezones /usr/share/zoneinfo altındaki timezone listesini döndürür.
func ListTimezones() []string {
	var zones []string
	base := "/usr/share/zoneinfo"

	regions := []string{
		"Africa", "America", "Antarctica", "Arctic", "Asia",
		"Atlantic", "Australia", "Europe", "Indian", "Pacific",
	}

	for _, region := range regions {
		entries, err := os.ReadDir(filepath.Join(base, region))
		if err != nil {
			continue
		}
		for _, e := range entries {
			if !e.IsDir() {
				zones = append(zones, region+"/"+e.Name())
			}
		}
	}

	sort.Strings(zones)
	return zones
}

// ListLocales /etc/locale.gen'deki UTF-8 locale'leri döndürür.
func ListLocales() []string {
	data, err := os.ReadFile("/etc/locale.gen")
	if err != nil {
		return []string{"tr_TR.UTF-8", "en_US.UTF-8"}
	}

	seen := map[string]bool{}
	var locales []string

	for _, line := range strings.Split(string(data), "\n") {
		line = strings.TrimSpace(strings.TrimPrefix(line, "#"))
		if line == "" || !strings.Contains(line, "UTF-8") {
			continue
		}
		parts := strings.Fields(line)
		if len(parts) > 0 && !seen[parts[0]] {
			seen[parts[0]] = true
			locales = append(locales, parts[0])
		}
	}

	if len(locales) == 0 {
		return []string{"tr_TR.UTF-8", "en_US.UTF-8"}
	}
	sort.Strings(locales)
	return locales
}
