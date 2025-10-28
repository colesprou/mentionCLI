"""
AI analysis and summarization features for market research.
"""

import openai
from typing import List, Dict, Any, Optional
import json
from datetime import datetime
from rich.console import Console
from textblob import TextBlob
import re

console = Console()

class AIAnalyzer:
    """AI-powered analysis for market research data."""
    
    def __init__(self, api_key: str, model: str = "gpt-4", max_tokens: int = 2000, temperature: float = 0.3):
        self.client = openai.OpenAI(api_key=api_key)
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
    
    async def analyze_market_data(self, market: Dict[str, Any], research_data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform comprehensive AI analysis on market and research data."""
        
        console.print(f"[blue]Running AI analysis for market: {market.get('title', 'Unknown')}[/blue]")
        
        # Prepare data for analysis
        analysis_input = self._prepare_analysis_input(market, research_data)
        
        # Run different types of analysis
        analyses = {
            'summary': await self._generate_summary(analysis_input),
            'sentiment': await self._analyze_sentiment(analysis_input),
            'prediction': await self._generate_prediction(analysis_input),
            'key_insights': await self._extract_key_insights(analysis_input),
            'similar_events': await self._find_similar_events(analysis_input)
        }
        
        # Combine all analyses
        combined_analysis = {
            'market_id': market.get('id'),
            'market_title': market.get('title'),
            'timestamp': datetime.utcnow().isoformat(),
            'analyses': analyses,
            'confidence_score': self._calculate_confidence(analyses)
        }
        
        console.print(f"[green]AI analysis completed for {market.get('title', 'Unknown')}[/green]")
        return combined_analysis
    
    async def generate_summary(self, prompt: str) -> str:
        """Generate a summary from a text prompt."""
        try:
            response = await self._call_openai(prompt)
            return response
        except Exception as e:
            console.print(f"[red]Error generating summary: {e}[/red]")
            return f"Error generating summary: {e}"
    
    def _prepare_analysis_input(self, market: Dict[str, Any], research_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare data for AI analysis."""
        
        # Extract all text content
        all_content = []
        
        # Add market information
        market_text = f"Market: {market.get('title', '')}\nDescription: {market.get('description', '')}"
        all_content.append(market_text)
        
        # Add research data
        for source, data in research_data.get('data', {}).items():
            for item in data:
                content_parts = []
                if item.get('title'):
                    content_parts.append(f"Title: {item['title']}")
                if item.get('content'):
                    content_parts.append(f"Content: {item['content'][:1000]}...")  # Truncate for token limits
                if item.get('summary'):
                    content_parts.append(f"Summary: {item['summary']}")
                
                if content_parts:
                    all_content.append(f"{source.upper()}: {' '.join(content_parts)}")
        
        return {
            'market': market,
            'research_data': research_data,
            'combined_text': '\n\n'.join(all_content),
            'keywords': research_data.get('keywords', [])
        }
    
    async def _generate_summary(self, analysis_input: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a comprehensive summary of the market and research data."""
        
        prompt = f"""
        Analyze the following market and research data to create a comprehensive summary:
        
        {analysis_input['combined_text'][:4000]}  # Truncate to avoid token limits
        
        Please provide:
        1. A 2-3 sentence executive summary
        2. Key facts about the market
        3. Main themes from the research data
        4. Recent developments or news
        5. Overall assessment of market sentiment
        
        Format your response as JSON with these keys: executive_summary, key_facts, main_themes, recent_developments, sentiment_assessment
        """
        
        try:
            response = await self._call_openai(prompt)
            return self._parse_json_response(response, {
                'executive_summary': 'Unable to generate summary',
                'key_facts': [],
                'main_themes': [],
                'recent_developments': [],
                'sentiment_assessment': 'neutral'
            })
        except Exception as e:
            console.print(f"[red]Error generating summary: {e}[/red]")
            return {'error': str(e)}
    
    async def _analyze_sentiment(self, analysis_input: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze sentiment across all data sources."""
        
        prompt = f"""
        Analyze the sentiment of the following market and research data:
        
        {analysis_input['combined_text'][:3000]}
        
        Please provide:
        1. Overall sentiment (bullish, bearish, neutral)
        2. Confidence level (0-100)
        3. Key positive indicators
        4. Key negative indicators
        5. Sentiment by source (news, social media, transcripts)
        
        Format your response as JSON with these keys: overall_sentiment, confidence, positive_indicators, negative_indicators, source_sentiments
        """
        
        try:
            response = await self._call_openai(prompt)
            return self._parse_json_response(response, {
                'overall_sentiment': 'neutral',
                'confidence': 50,
                'positive_indicators': [],
                'negative_indicators': [],
                'source_sentiments': {}
            })
        except Exception as e:
            console.print(f"[red]Error analyzing sentiment: {e}[/red]")
            return {'error': str(e)}
    
    async def _generate_prediction(self, analysis_input: Dict[str, Any]) -> Dict[str, Any]:
        """Generate prediction about market outcome."""
        
        prompt = f"""
        Based on the following market and research data, provide a prediction about the market outcome:
        
        Market: {analysis_input['market'].get('title', '')}
        Description: {analysis_input['market'].get('description', '')}
        
        Research Data:
        {analysis_input['combined_text'][:3000]}
        
        Please provide:
        1. Predicted outcome (yes/no with confidence percentage)
        2. Key factors supporting this prediction
        3. Potential risks or uncertainties
        4. Timeline considerations
        5. Alternative scenarios
        
        Format your response as JSON with these keys: predicted_outcome, confidence, supporting_factors, risks, timeline, alternative_scenarios
        """
        
        try:
            response = await self._call_openai(prompt)
            return self._parse_json_response(response, {
                'predicted_outcome': 'unknown',
                'confidence': 50,
                'supporting_factors': [],
                'risks': [],
                'timeline': 'unknown',
                'alternative_scenarios': []
            })
        except Exception as e:
            console.print(f"[red]Error generating prediction: {e}[/red]")
            return {'error': str(e)}
    
    async def _extract_key_insights(self, analysis_input: Dict[str, Any]) -> Dict[str, Any]:
        """Extract key insights from the research data."""
        
        prompt = f"""
        Extract key insights from the following market research data:
        
        {analysis_input['combined_text'][:3000]}
        
        Please identify:
        1. Most important facts or developments
        2. Surprising or unexpected information
        3. Patterns or trends
        4. Contradictions or conflicting information
        5. Actionable insights for traders
        
        Format your response as JSON with these keys: important_facts, surprising_info, patterns, contradictions, actionable_insights
        """
        
        try:
            response = await self._call_openai(prompt)
            return self._parse_json_response(response, {
                'important_facts': [],
                'surprising_info': [],
                'patterns': [],
                'contradictions': [],
                'actionable_insights': []
            })
        except Exception as e:
            console.print(f"[red]Error extracting insights: {e}[/red]")
            return {'error': str(e)}
    
    async def _find_similar_events(self, analysis_input: Dict[str, Any]) -> Dict[str, Any]:
        """Find similar historical events or patterns."""
        
        prompt = f"""
        Based on the following market and research data, identify similar historical events or patterns:
        
        {analysis_input['combined_text'][:3000]}
        
        Please identify:
        1. Similar historical events or situations
        2. How those events turned out
        3. Key similarities and differences
        4. Lessons learned from similar events
        5. What to watch for based on historical patterns
        
        Format your response as JSON with these keys: similar_events, outcomes, similarities, differences, lessons, watch_points
        """
        
        try:
            response = await self._call_openai(prompt)
            return self._parse_json_response(response, {
                'similar_events': [],
                'outcomes': [],
                'similarities': [],
                'differences': [],
                'lessons': [],
                'watch_points': []
            })
        except Exception as e:
            console.print(f"[red]Error finding similar events: {e}[/red]")
            return {'error': str(e)}
    
    async def _call_openai(self, prompt: str) -> str:
        """Make a call to OpenAI API."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert financial analyst and market researcher. Provide accurate, data-driven analysis in JSON format."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            return response.choices[0].message.content
        except Exception as e:
            console.print(f"[red]OpenAI API error: {e}[/red]")
            raise
    
    def _parse_json_response(self, response: str, default: Dict[str, Any]) -> Dict[str, Any]:
        """Parse JSON response from OpenAI, with fallback to default."""
        try:
            # Try to extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return default
        except json.JSONDecodeError:
            console.print(f"[yellow]Could not parse JSON response: {response[:200]}...[/yellow]")
            return default
    
    def _calculate_confidence(self, analyses: Dict[str, Any]) -> float:
        """Calculate overall confidence score for the analysis."""
        confidence_scores = []
        
        for analysis_type, analysis_data in analyses.items():
            if isinstance(analysis_data, dict) and 'confidence' in analysis_data:
                confidence_scores.append(analysis_data['confidence'])
            elif isinstance(analysis_data, dict) and 'error' not in analysis_data:
                # If no explicit confidence, estimate based on data quality
                confidence_scores.append(70)  # Default moderate confidence
        
        if confidence_scores:
            return sum(confidence_scores) / len(confidence_scores)
        else:
            return 50  # Default low confidence

class SentimentAnalyzer:
    """Traditional sentiment analysis using TextBlob and other methods."""
    
    def __init__(self):
        pass
    
    def analyze_text_sentiment(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment of text using TextBlob."""
        if not text:
            return {'polarity': 0, 'subjectivity': 0, 'sentiment': 'neutral'}
        
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity
        subjectivity = blob.sentiment.subjectivity
        
        if polarity > 0.1:
            sentiment = 'positive'
        elif polarity < -0.1:
            sentiment = 'negative'
        else:
            sentiment = 'neutral'
        
        return {
            'polarity': polarity,
            'subjectivity': subjectivity,
            'sentiment': sentiment,
            'confidence': abs(polarity)
        }
    
    def analyze_batch_sentiment(self, texts: List[str]) -> Dict[str, Any]:
        """Analyze sentiment for multiple texts."""
        sentiments = [self.analyze_text_sentiment(text) for text in texts]
        
        if not sentiments:
            return {'overall_sentiment': 'neutral', 'average_polarity': 0, 'confidence': 0}
        
        avg_polarity = sum(s['polarity'] for s in sentiments) / len(sentiments)
        avg_subjectivity = sum(s['subjectivity'] for s in sentiments) / len(sentiments)
        
        if avg_polarity > 0.1:
            overall_sentiment = 'positive'
        elif avg_polarity < -0.1:
            overall_sentiment = 'negative'
        else:
            overall_sentiment = 'neutral'
        
        return {
            'overall_sentiment': overall_sentiment,
            'average_polarity': avg_polarity,
            'average_subjectivity': avg_subjectivity,
            'confidence': abs(avg_polarity),
            'individual_sentiments': sentiments
        }


