# NOTE: the ONE place MediaGrab's own version lives - Settings -> Version
# Checks compares it against the latest GitHub release, and the About page
# shows it. Bump it together with CHANGELOG.md's newest "### [x.y.z]" entry
# when tagging a release; tests/test_version.py fails if the two disagree.
__version__ = "2.3.0"
