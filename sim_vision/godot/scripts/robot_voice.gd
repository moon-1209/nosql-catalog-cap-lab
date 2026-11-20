class_name RobotVoice
extends AudioStreamPlayer3D
## Loa trên đầu robot (G22). `say(stream)` phát câu trả lời; xong phát `finished_speaking` (cả khi bị `stop_speaking`).

signal finished_speaking

var speaking: bool = false


func _ready() -> void:
	finished.connect(_on_finished)


func say(stream: AudioStream) -> void:
	self.stream = stream
	speaking = true
	play()


func stop_speaking() -> void:
	if speaking:
		stop()
		_on_finished()


func _on_finished() -> void:
	if speaking:
		speaking = false
		finished_speaking.emit()
