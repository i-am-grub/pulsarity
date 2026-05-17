Running the Full Stack Application
===================================

The front-end and back-end applications of Pulsarity live
in seperate repos and are only bundled together at release
time. 

Running the application directly after cloning the
repository will result in the back-end only serving the
API connections. In order for the application to also serve
the front-end, the built files should be added to the
``~/src/pulsarity/frontend`` directory of the project.
The primary ``index.html`` file of the servable files should 
be located at ``~/src/pulsarity/frontend/index.html``.

An approach to making these built files avalible to the
back-end automatically is by setting up a symbolic link
from the front-end build folder pointing to 
``~/src/pulsarity/frontend``.
