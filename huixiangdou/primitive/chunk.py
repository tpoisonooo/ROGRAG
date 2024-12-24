from dataclasses import dataclass, field
import uuid
import hashlib

@dataclass
class Chunk():
    """Class for storing a piece of text and associated metadata.

    Example:

        .. code-block:: python

            from huixiangdou.primitive import Chunk

            chunk = Chunk(
                content_or_path="Hello, world!",
                metadata={"source": "https://example.com"}
            )
    """
    # fixed attribute sequence
    _hash: str = field(default_factory=lambda: str(uuid.uuid4())[0:6])
    content_or_path: str = ''
    metadata: dict = field(default_factory=dict)
    modal: str = 'text'

    def __post_init__(self):
        if self.modal not in ['text', 'image', 'audio', 'fasta']:
            raise ValueError(
                f'Invalid modal: {self.modal}. Allowed values are: `text`, `image`, `audio`'
            )
        md5 = hashlib.md5()
        if type(self.content_or_path) is str:
            md5.update(self.content_or_path.encode('utf8'))
        else:
            md5.update(self.content_or_path)
        self._hash = md5.hexdigest()[0:6]

    def __str__(self) -> str:
        """Override __str__ to restrict it to content_or_path and metadata."""
        # The format matches pydantic format for __str__.
        #
        # The purpose of this change is to make sure that user code that
        # feeds Document objects directly into prompts remains unchanged
        # due to the addition of the id field (or any other fields in the future).
        #
        # This override will likely be removed in the future in favor of
        # a more general solution of formatting content directly inside the prompts.
        if self.metadata:
            return f"modal='{self.modal}' content_or_path='{self.content_or_path}' metadata={self.metadata}"
        else:
            return f"modal='{self.modal}' content_or_path='{self.content_or_path}'"

    def __repr__(self) -> str:
        return self.__str__()


if __name__ == "__main__":
    obj = Chunk(content_or_path="abc")
    import pickle
    pickled_obj = pickle.dumps([obj])
    print(pickled_obj)
