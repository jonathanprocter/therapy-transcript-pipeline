import asyncio
from unittest.mock import AsyncMock, patch

from ai_service import AIService
from background_tasks import BackgroundTaskQueue


def test_analyze_transcript_async():
    service = AIService()

    async def run():
        with patch.object(service, '_analyze_with_openai', return_value={'openai': True}), \
             patch.object(service, '_analyze_with_anthropic', return_value={'anthropic': True}), \
             patch.object(service, '_analyze_with_gemini', return_value={'gemini': True}), \
             patch.object(service, '_consolidate_insights', return_value={'summary': 'ok'}):
            result = await service.analyze_transcript_async('text')
        return result

    result = asyncio.run(run())
    assert result['openai_analysis'] == {'openai': True}
    assert result['anthropic_analysis'] == {'anthropic': True}
    assert result['gemini_analysis'] == {'gemini': True}
    assert result['consolidated_insights'] == {'summary': 'ok'}


def test_background_task_queue():
    async def run_queue():
        queue = BackgroundTaskQueue()
        await queue.start()
        flag = {'done': False}

        async def task():
            flag['done'] = True

        await queue.add_task(task())
        await asyncio.sleep(0.05)
        await queue.stop()
        return flag['done']

    done = asyncio.run(run_queue())
    assert done

