from dataclasses import dataclass

@dataclass
class MetaData:
	file: File
	line: int
	column: int

	def to_str(self):
		return f'"{self.file.name}":{self.line}:{self.column}'

	def __str__(self):
		return f'MetaData(file={self.file}, line={self.line}, column={self.column})'

	def __repr__(self):
		return f'MetaData(file={self.file}, line={self.line}, column={self.column})'


@dataclass
class File:
	name: str
	content: str

	def __str__(self):
		return f'File("{self.name}")'

	def __repr__(self):
		return f'File("{self.name}")'