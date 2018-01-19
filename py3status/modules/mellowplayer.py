# -*- coding: utf-8 -*-
"""
Display song currently playing in mellowplayer. (fork from spotify module)

Configuration parameters:
    cache_timeout: how often to update the bar (default 5)
    format: see placeholders below (default '{artist} : {title}')
    format_down: define output if mellowplayer is not running
        (default 'mellowplayer not running')
    format_stopped: define output if mellowplayer is not playing
        (default 'mellowplayer stopped')
    sanitize_titles: whether to remove meta data from album/track title
        (default True)
    sanitize_words: which meta data to remove
        (default ['bonus', 'demo', 'edit', 'explicit',
                  'extended', 'feat', 'mono', 'remaster',
                  'stereo', 'version'])

Format placeholders:
    {album} album name
    {artist} artiste name (first one)
    {time} time duration of the song
    {title} name of the song

Color options:
    color_offline: mellowplayer is not running, defaults to color_bad
    color_paused: Song is stopped or paused, defaults to color_degraded
    color_playing: Song is playing, defaults to color_good

i3status.conf example:

```
mellowplayer {
    format = "{title} by {artist} {time}"
    format_down = "no mellowplayer"
}
```

Requires:
    mellowplayer (>= 3.3.1.0, depend on service)

@author Pierre Guilbert, Jimmy Garpehäll, sondrele, Andrwe, Cyril Levis

SAMPLE OUTPUT
{'color': '#00FF00', 'full_text': 'Rick Astley : Never Gonna Give You Up'}

paused
{'color': '#FFFF00', 'full_text': 'Rick Astley : Never Gonna Give You Up'}

stopped
{'color': '#FF0000', 'full_text': 'mellowplayer stopped'}
"""

from datetime import timedelta
import dbus
import re


class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 5
    format = '{artist} : {title}'
    format_down = 'MellowPlayer not running'
    format_stopped = 'MellowPlayer stopped'
    sanitize_titles = True
    sanitize_words = [
        'bonus', 'demo', 'edit', 'explicit', 'extended', 'feat', 'mono',
        'remaster', 'stereo', 'version'
    ]

    def post_config_hook(self):
        """
        """
        # Match string after hyphen, comma, semicolon or slash containing any metadata word
        # examples:
        # - Remastered 2012
        # / Radio Edit
        # ; Remastered
        self.after_delimiter = self._compile_re(
            r"([\-,;/])([^\-,;/])*(META_WORDS_HERE).*")

        # Match brackets with their content containing any metadata word
        # examples:
        # (Remastered 2017)
        # [Single]
        # (Bonus Track)
        self.inside_brackets = self._compile_re(
            r"([\(\[][^)\]]*?(META_WORDS_HERE)[^)\]]*?[\)\]])")

    def _compile_re(self, expression):
        """
        Compile given regular expression for current sanitize words
        """
        meta_words = '|'.join(self.sanitize_words)
        expression = expression.replace('META_WORDS_HERE', meta_words)
        return re.compile(expression, re.IGNORECASE)

    def _get_text(self):
        """
        Get the current song metadatas (artist - title)
        """
        bus = dbus.SessionBus()
        try:
            self.__bus = bus.get_object('org.mpris.MediaPlayer2.MellowPlayer',
                                        '/org/mpris/MediaPlayer2')
            self.player = dbus.Interface(self.__bus,
                                         'org.freedesktop.DBus.Properties')

            try:
                metadata = self.player.Get('org.mpris.MediaPlayer2.Player',
                                           'Metadata')
                album = metadata.get('xesam:album')
                artist = metadata.get('xesam:artist')[0]
                microtime = metadata.get('mpris:length')
                rtime = str(timedelta(microseconds=microtime))[:-7]
                title = metadata.get('xesam:title')
                if self.sanitize_titles:
                    album = self._sanitize_title(album)
                    title = self._sanitize_title(title)

                playback_status = self.player.Get(
                    'org.mpris.MediaPlayer2.Player', 'PlaybackStatus')
                if playback_status.strip() == 'Playing':
                    color = self.py3.COLOR_PLAYING or self.py3.COLOR_GOOD
                else:
                    color = self.py3.COLOR_PAUSED or self.py3.COLOR_DEGRADED
            except Exception:
                return (self.format_stopped, self.py3.COLOR_PAUSED
                        or self.py3.COLOR_DEGRADED)

            return (self.py3.safe_format(self.format,
                                         dict(
                                             title=title,
                                             artist=artist,
                                             album=album,
                                             time=rtime)), color)
        except Exception:
            return (self.format_down, self.py3.COLOR_OFFLINE
                    or self.py3.COLOR_BAD)

    def _sanitize_title(self, title):
        """
        Remove redunant meta data from title and return it
        """
        title = re.sub(self.inside_brackets, "", title)
        title = re.sub(self.after_delimiter, "", title)
        return title.strip()

    def mellowplayer(self):
        """
        Get the current "artist - title" and return it.
        """
        (text, color) = self._get_text()
        response = {
            'cached_until': self.py3.time_in(self.cache_timeout),
            'color': color,
            'full_text': text
        }
        return response


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
