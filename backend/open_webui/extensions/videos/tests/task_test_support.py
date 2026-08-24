from open_webui.extensions.videos.schemas import VideoTaskResponse


class FileUrlRequest:
    class _App:
        @staticmethod
        def url_path_for(_name: str, *, id: str) -> str:
            return f'/api/v1/files/{id}/content'

    app = _App()


def video_task() -> VideoTaskResponse:
    return VideoTaskResponse(
        id='task-1',
        status='running',
        task='text-to-video',
        prompt='A paper boat',
        model_id='kling-video-v3-pro',
        params={'duration': '5'},
        assets=(),
        result=None,
        error_code=None,
        created_at=1,
        updated_at=1,
    )


__all__ = ['FileUrlRequest', 'video_task']
