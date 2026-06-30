import '../App.css';
import PropTypes from 'prop-types';

export default function Container({ children }) {
  return (
    <div className=" bg-white rounded-[1.25rem] border-[0.063rem] border-black h-full overflow-visible">
      {children}
    </div>
  );
}

Container.propTypes = {
  children: PropTypes.node,
};
