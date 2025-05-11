try:
    import pyglet
    from pyglet.gl import GL_LINEAR

    pyglet.image.Texture.default_min_filter = GL_LINEAR
    pyglet.image.Texture.default_mag_filter = GL_LINEAR

    from .context import context
    from .application import Window
    from .views.menu import MainMenuView
except (Exception, KeyboardInterrupt) as e:
    from datetime import datetime
    import traceback
    from uuid import uuid4
    crash_time = datetime.now().strftime("%Y-%m-%d %H-%M")
    with open(f"early-crash-{crash_time}_{uuid4().hex}.txt", "w", encoding="utf-8") as fp:
        fp.write("".join(traceback.format_exception(e)))
    raise e from e


def main() -> None:
    try:
        win = Window()
        win.show_view(MainMenuView())
        win.run()
    except (Exception, KeyboardInterrupt) as e:
        context.log_fatal_exception(e)
        raise e from e
    context.close()
