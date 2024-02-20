import subprocess

import click

LANGUAGES = ['de']


@click.command(help='Creates and updates localization files')
@click.option(
    '--init',
    '-i',
    is_flag=True,
    help='(Re-)Init a translation file for all languages. (Caution: this will override any existing translations!)',
)
@click.option('--poEditPath', '-p', help='Path to the Poedit executable')
def update_localization(init, poeditpath):
    print('Extracting messages...')
    subprocess.run(
        ['pybabel', 'extract', '-F', 'babel.cfg', '-o', 'messages.pot', '../'], check=True
    )

    for language in LANGUAGES:
        if init:
            print(f'Initializing translation for "{language}"...')
            subprocess.run(
                ['pybabel', 'init', '-i', 'messages.pot', '-d', '.', '-l', language], check=True
            )

        print(f'Updating translation for "{language}"...')
        subprocess.run(
            ['pybabel', 'update', '-i', 'messages.pot', '-d', '.', '-l', language], check=True
        )

        if poeditpath is not None:
            print(f'Opening Poedit for language "{language}"...')
            subprocess.run([poeditpath, 'de/LC_MESSAGES/messages.po'], check=True)

    print('Compiling translations...')
    subprocess.run(['pybabel', 'compile', '-d', '.'], check=True)
    print('DONE')


if __name__ == '__main__':
    update_localization()
