fleetpy
=======
An opinionated fleet API client for Python.

:boom:**Important**:boom: This project is deprecated and no longer maintained. If you'd like to take it over, please contact me.

Usage
-----

.. code:: python

    import fleetpy

    client = fleetpy.Client('https://fleet.myenv.com')
    unit = client.unit('consul', from_file='consul.service')

    # Submit the unit, but keep it inactive
    unit.submit()

    # Start the unit
    unit.start()

    # Stop the unit
    unit.stop()

    # List the state of all units
    state = client.state()

    # List the machines
    machines = client.machines()

    # List the units
    units = client.units()

    # Get the state of a remote unit
    unit = client.unit('remote.service')
    unit.refresh()
    print(unit.state)
