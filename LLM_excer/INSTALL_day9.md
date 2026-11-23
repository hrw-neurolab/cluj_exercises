# Tag 9: Was installiert sein muss

## Teil 1: Korridor (`python3 llm_robot_agent.py`)

Dafür brauchst du kein ROS. Es reichen Ollama, ein Modell und ein Python Paket.

**1. Ollama installieren**

```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama -v
```

Danach läuft Ollama als Dienst auf Port 11434. Das ist die `base_url` in `llm_robot_agent.py`.

**2. Modell laden**

```bash
ollama pull qwen3:8b       # 5,2 GB, 40K Kontext
# oder
ollama pull gemma4:e4b     # 6,6 bis 9,5 GB, 128K Kontext
```

Mit `ollama show qwen3:8b` siehst du, ob unter Capabilities `tools` steht. In `llm_robot_agent.py` steht `MODEL = "gemma4:e4b"`. Wenn du Qwen nimmst, setze dort `MODEL = "qwen3:8b"`.

**3. Python Umgebung**

```bash
cd ~/ros_workspace/day9            # Ordner mit den vier .py Dateien
python3 -m venv --system-site-packages .venv
source .venv/bin/activate
pip install openai                 # getestet mit 3.42.1
python3 llm_robot_agent.py
```

`--system-site-packages` ist erst für Teil 2 wichtig. Damit sieht die venv die Python Pakete, die ROS über apt installiert hat.

**GPU:** `nvidia-smi` sollte deine Karte anzeigen. Ohne passende GPU rechnet Ollama auf der CPU. Das funktioniert, ist aber deutlich langsamer.

## Teil 2: Roboter mit Nav2 (`python3 llm_robot_agent.py nav2`)

Teil 2 nutzt kein Gazebo, sondern die Welt aus dem ROS Paket `delivery_bt` von Tag 8. Das ist ein kleiner Simulator mit Batterie und Dock, dazu kommen Karte, AMCL, Nav2 und RViz. Wenn `delivery_bt` an Tag 8 lief, musst du nichts Neues installieren. Setup und Build stehen im README des Pakets. `nav2_robot.py` braucht noch `nav2_simple_commander`, das steckt in `navigation2`:

```bash
sudo apt install ros-kilted-navigation2
```

**Terminal 1: die Welt starten**

```bash
cd ~/ros_workspace/src/delivery_bt
source /opt/ros/kilted/setup.bash
source install/setup.bash
ros2 launch delivery_bt delivery.launch.py world:=room
```

`world:=room` ist der Raum von Tag 6 mit der Innenwand. Der Roboter startet auf dem Dock, und das Dock ist der Ursprung der Karte. AMCL startet auch dort, eine 2D Pose Estimate in RViz brauchst du also nicht.

**Terminal 2: das LLM starten**

```bash
cd ~/ros_workspace/day9
source /opt/ros/kilted/setup.bash
source .venv/bin/activate
python3 llm_robot_agent.py nav2
```

Die Stationen in `nav2_robot.py` sind schon eingetragen, als Posen der Welt `room` im Frame `map`: Dock (0.0, 0.0), Pickup (-0.7, 1.5), Dropoff (3.9, 1.3). Für die Welt `loop` (Launch ohne `world:=room`) setzt du dort Pickup (4.0, 0.0) und Dropoff (4.0, -4.0) ein.

**Eigene Punkte auf der Karte finden:** Starte in einem dritten Terminal (ROS gesourct):

```bash
ros2 topic echo /clicked_point
```

Wähle dann in RViz oben in der Werkzeugleiste „Publish Point“ und klicke auf die Karte. Das Terminal zeigt den Punkt im Frame `map`. `point.x` und `point.y` trägst du in `STATIONS` in `nav2_robot.py` ein, mit Dezimalpunkt (z. B. `2.0`).

**Batterie:** Der Simulator hat eine Batterie, und mit 70 % ist sie auf dem Rückweg vom Dropoff leer. Die Tools von Teil 2 kennen sie noch nicht, das ist die Aufgabe unten.

**Kilted statt Jazzy:** Die Folien verweisen auf Jazzy. Ich habe den Simple Commander im Kilted Branch geprüft. `BasicNavigator`, `goToPose`, `isTaskComplete`, `getResult` und `waitUntilNav2Active` haben dort dieselben Aufrufe. Der Code läuft also unverändert.

## Ohne GPU: Cloud statt lokal

In `llm_robot_agent.py` änderst du nur drei Werte: `base_url="https://ollama.com/v1"`, `api_key=os.environ["OLLAMA_API_KEY"]` (dafür zusätzlich `import os`) und `MODEL`, z. B. `gemma4:31b`.

## Aufgabe: Batterie für Teil 2

Der Simulator von `delivery_bt` hat eine Batterie. Sie startet mit 70 % und verbraucht im Raum 9 % pro Meter. Probier es aus: Mit den Tools von Teil 2 kommt der Roboter noch bis zum Dropoff, auf dem Rückweg ist die Batterie leer. Der Simulator meldet `Battery empty! The robot stops.`, Nav2 gibt auf, und `goto` meldet `failed to reach dock`. Das LLM hat keine Chance, denn es kann die Batterie weder abfragen noch laden.

**Deine Aufgabe:** Gib dem LLM zwei neue Tools, so wie `status` und `charge` in Teil 1:

| Tool | Was es tut |
|---|---|
| `battery` | gibt den Ladestand zurück, z. B. `battery 54 %` |
| `charge` | lädt am Dock auf 100 % und antwortet erst, wenn die Batterie voll ist. Nicht am Dock meldet es einen Fehler |

Dafür änderst du drei Dateien:

1. `nav2_robot.py`: die zwei Python Funktionen schreiben und in `FUNCTIONS` eintragen.
2. `tool_descriptions.py`: zwei Einträge in `NAV2_TOOLS`. Beide Tools haben keine Parameter, wie `charge` und `status` in `CORRIDOR_TOOLS`.
3. `llm_robot_agent.py`: `NAV2_SYSTEM_PROMPT` ergänzen, damit das LLM auf die Batterie achtet und weiß, dass Laden nur am Dock geht.

**Was der Simulator anbietet:**

| Name | Typ | Bedeutung |
|---|---|---|
| Topic `/battery_state` | `sensor_msgs/msg/BatteryState` | `percentage` von 0 bis 1, also 0.54 heißt 54 % |
| Service `/dock/charge` | `std_srvs/srv/Trigger` | startet das Laden, nur auf dem Dock (näher als 0.35 m). `success` und `message` der Antwort sagen, ob es geklappt hat |

Probier beides vorher von Hand aus, während die Welt läuft:

```bash
ros2 topic echo /battery_state --field percentage
ros2 service call /dock/charge std_srvs/srv/Trigger
```

**Tipps:**

- `navigator` ist selbst ein ROS Node. In `connect()` legst du damit eine Subscription und einen Service Client an: `navigator.create_subscription(...)` und `navigator.create_client(...)`. Die Callback Funktion der Subscription merkt sich den letzten Ladestand.
- Callbacks laufen nur, wenn jemand den Node spinnt. `rclpy.spin_once(navigator, timeout_sec=0.5)` macht einen Durchlauf. Auf die Antwort eines Service wartest du mit `rclpy.spin_until_future_complete(navigator, future)`.
- `/dock/charge` startet das Laden nur und antwortet sofort. Geladen wird, bis die Batterie voll ist oder der Roboter losfährt. `charge` muss also selbst warten, bis `/battery_state` 100 % meldet, sonst fährt das LLM mit halb voller Batterie weiter. Der Simulator lädt 10 % pro Sekunde.

**Fertig** bist du, wenn das LLM die Box abliefert und der Roboter mit Batterie am Dock ankommt. Im Bericht soll stehen, wann und warum es geladen hat.

**Zum Testen:**

- Mit `battery:=30.0` am Launch sollte das LLM gleich am Anfang laden.
- Mit `ros2 param set /drive_sim battery 20.0` wird die Batterie mitten in der Mission knapp.
- Ist sie leer, lädst du von Hand mit `ros2 param set /drive_sim battery 100.0`.

**Bonus:** Lass `goto` nach jeder Fahrt den Ladestand mitmelden, wie in Teil 1 (`at pickup, battery 55 %`). Braucht das LLM dann `battery` noch?
