import ScalarFieldLayer from './ScalarFieldLayer';
import { getTemperatureColor } from '../../utils/temperatureColorScale';

export default function TemperatureLayer(props) {
  return <ScalarFieldLayer {...props} parameter="temperature" colorScale={getTemperatureColor} />;
}
