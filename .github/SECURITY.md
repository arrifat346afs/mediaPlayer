# Security policy

Report vulnerabilities privately through
[GitHub security advisories](https://github.com/bernardopg/mediaPlayer/security/advisories/new),
not in public issues. Only the latest release is supported.

The widget reads media state from Dux Shell's services. Its own code starts
no processes, makes no network requests and writes no files; remote album art
is fetched and cached by the shell's `TrackArtService`, the same one the bar
and dash use. A report of the plugin doing any of those itself points to a
regression worth hearing about.
