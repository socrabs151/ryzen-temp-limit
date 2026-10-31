# Privacy

Ryzen Temp Limit does not collect or transmit personal data, telemetry or
usage statistics.

- CPU temperature, power and clock values are read locally from the SMU.
- Settings, logs and downloaded updates stay on the local machine.
- The update checker sends an HTTPS request to the public GitHub Releases API.
  GitHub may log the IP address as part of normal server operation; no other
  network requests are made by the application.
- There are no analytics, ads or third-party trackers.

Uninstalling is described in the README: remove the background task, close the
application, delete its folder and the data directory.
